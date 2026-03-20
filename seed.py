from app import app, db
from models import User

def seed_data():
    with app.app_context():
        # Clear existing data to start fresh
        db.drop_all()
        db.create_all()

        users = [
            User(
                username='Alice', 
                email='alice@example.com', 
                password='password123', 
                gender='Female', 
                interest='Male', 
                interests_list='coding,hiking,coffee',
                image_file='alice.png',
                bio='Software engineer looking for a hiking partner.'
            ),
            User(
                username='Bob', 
                email='bob@example.com', 
                password='password123', 
                gender='Male', 
                interest='Female', 
                interests_list='coding,gaming,pizza',
                image_file='bob.png',
                bio='I love Python and late-night gaming sessions.'
            ),
            User(
                username='Charlie', 
                email='charlie@example.com', 
                password='password123', 
                gender='Male', 
                interest='Female', 
                interests_list='hiking,photography,travel',
                image_file='charlie.png',
                bio='Capturing the world through my lens.'
            ),
            User(
                username='Diana', 
                email='diana@example.com', 
                password='password123', 
                gender='Female', 
                interest='Male', 
                interests_list='music,dancing,coffee',
                image_file='diana.png',
                bio='Always looking for a new playlist or a dance floor.'
            )
        ]

        db.session.add_all(users)
        db.session.commit()
        print("Database seeded successfully with 4 test users!")

if __name__ == '__main__':
    seed_data()