from firebase_admin import credentials, initialize_app, db, firestore, auth, GoogleAuthCredentials
import os, json

if False:


    envVarPath = os.environ.get('FamilyTreeCred')
    envVar = None
    with open(envVarPath, 'r') as f:
        envVar = json.load(f)

    cred = credentials.Certificate(envVar)
    initialize_app(cred)

    db = firestore.client()

    requestRef = db.collection('requests')
    members_ref = db.collection('members')
    print("loaded!")
else:
    envVar = os.environ.get('FamilyTreeCred')

    cred = credentials.Certificate(json.loads(envVar))
    initialize_app(cred)

    db = firestore.client()

    requestRef = db.collection('requests')
    members_ref = db.collection('members')
    print("loaded!")
    
    

def GmailListed(email):
    
    try:
        auth.get_user_by_email(email)
        return True
    except auth.UserNotFoundError:
        return False
    except Exception as e:
        print(e)
        return False
    
def Verified(gmail):
    
    try:
        user = auth.get_user_by_email(gmail)
        return requestRef.document(user.uid).get().to_dict().get('verified', False)
    except Exception as e:
        print(e)
        return False

def VerifiedUid(uid):
    
    try:
        return requestRef.document(uid).get().to_dict().get('verified', False)
    except Exception as e:
        print(e)
        return False
    
def UidInRequests(uid):
    
    try:
        return requestRef.document(uid).get().exists
    except Exception as e:
        print(e)
        return False

def signup(email, password):
    
    try:
        user = auth.create_user(
            email=email,
            password=password
        )

        if Verified(email):
            return user.uid, True

        requestRef.add({
            'uid': user.uid,
            'email': email,
            'verified': False,
            'password': password
        },
        user.uid
        )

        return user.uid, False
    
    except Exception as e:
        print(e)
        return None, False

def login(email, password):
    
    try:
        user = auth.get_user_by_email(email)
        if Verified(email):
            if db.collection('requests').document(user.uid).get().to_dict().get('password') == password:
                return user.uid, True, True
            else:
                return user.uid, True, False
        else:
            if db.collection('requests').document(user.uid).get().to_dict().get('password') == password:
                return user.uid, False, True
            else:
                return user.uid, False, False
        
    except Exception as e:
        print(e)
        return None, None, None

def add_member(name, uniqueId = 0, gender = '', birthDate = ''):
    
    members_ref.document(f"{name.lower()} ^ {uniqueId}").set({
        'name': name,
        'gender': gender,
        'birthDate': birthDate,
        'uniqueId': uniqueId,
        'children': [],
        'parents': []
    })

def update_member(key, member = {}):
    new_key = f'{member.get("name").lower()} ^ {member.get("uniqueId")}'
    if new_key != key:
        for child_key in member['children']:
            child = members_ref.document(child_key).get().to_dict()
            parents = child['parents']
            parents.remove(key)
            parents.append(new_key)
            members_ref.document(child_key).update({'parents': parents})
        
        for parent_key in member['parents']:
            parent = members_ref.document(parent_key).get().to_dict()
            children = parent['children']
            children.remove(key)
            children.append(new_key)
            members_ref.document(parent_key).update({'children': children})
    
        members_ref.document(key).delete()
        members_ref.document(new_key).set(member)
    else:
        members_ref.document(key).update(member)

def check_member(name, uniqueId = 0):
    
    return members_ref.document(f"{name} ^ {uniqueId}").get().exists

def get_member(name, uniqueId = 0):
    return members_ref.document(f"{name} ^ {uniqueId}").get().to_dict()

def get_all_members():
    
    members = {}
    for member in members_ref.get():
        members[member.id] = member.to_dict()
    return members


def delete_member(key):
    member = members_ref.document(key).get().to_dict()
    
    # print(member['children'])
    for child in member['children']:
        parents = members_ref.document(child).get().to_dict()['parents']
        parents.remove(key)
        members_ref.document(child).update({'parents': parents})
        # print(parents)
    
    # print(member['parents'])
    
    for parent in member['parents']:
        children = members_ref.document(parent).get().to_dict()['children']
        children.remove(key)
        members_ref.document(parent).update({'children': children})
        # print(children)
        
    members_ref.document(key).delete()

def get_all_requests():
    
    requests = {}
    for request in requestRef.get():
        requests[request.id] = request.to_dict()
    return requests

def update_request(uid, data):
    
    requestRef.document(uid).update(data)