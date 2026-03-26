from firebase_admin import credentials, initialize_app, db, firestore, auth, GoogleAuthCredentials
import os, json

requestRef: firestore.CollectionReference = None
members_ref: firestore.CollectionReference = None
cred = None
db = None


def load_firebase():
    global requestRef, members_ref, db, cred
    try:
        envVarDir = os.getenv('FamilyTreeCred')
        envVar = None
        with open(envVarDir, 'r') as f:
            envVar = json.load(f)

        # print(envVar)

        cred = credentials.Certificate(envVar)
        initialize_app(cred)

        db = firestore.client()

        requestRef = db.collection('requests')
        members_ref = db.collection('members')
    except Exception as e:
        print(e)
    
    

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
    if requestRef == None:
        load_firebase()
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
    if requestRef == None:
        load_firebase()
    try:
        user = auth.get_user_by_email(email)
        if Verified(email):
            if db.collection('requests').document(user.uid).get().to_dict().get('password') == password:
                return user.uid, True
        
        return user.uid, False
    except Exception as e:
        print(e)
        return None, None

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
    members_ref.document(key).delete()
    members_ref.document(f'{member.get("name").lower()} ^ {member.get("uniqueId")}').set(member)

def check_member(name, uniqueId = 0):
    return members_ref.document(f"{name} ^ {uniqueId}").get().exists

def get_member(name, uniqueId = 0):
    return members_ref.document(f"{name} ^ {uniqueId}").get().to_dict()

def get_all_members():
    members = {}
    for member in members_ref.get():
        members[member.id] = member.to_dict()
    return members

def get_all_requests():
    requests = {}
    for request in requestRef.get():
        requests[request.id] = request.to_dict()
    return requests

def update_request(uid, data):
    requestRef.document(uid).update(data)