from google.cloud import firestore


def fetch_all_user_keywords():
    db = firestore.Client()
    users = db.collection("users").stream()
    users_list = list(users)

    result = []
    for user in users_list:
        uid = user.id
        keywords_ref = db.collection("users").document(uid).collection("keywords")
        keywords = [doc.to_dict()["keyword"] for doc in keywords_ref.stream()]
        if keywords:
            result.append({"user_id": uid, "keywords": keywords})
    
    print(f"result {result}")
    return result
