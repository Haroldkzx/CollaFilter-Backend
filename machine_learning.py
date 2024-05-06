import pandas as pd
from surprise import KNNBasic, Dataset, Reader, accuracy
from collections import defaultdict
from operator import itemgetter
import heapq
from pymongo import MongoClient
from uuid import UUID
import random

class CollaFilterRecommender:
    def __init__(self, db_uri, db_name):
        self.client = MongoClient(db_uri, uuidRepresentation='standard')
        self.db = self.client[db_name]
        self.products_collection = self.db['products']
        self.ratings_collection = self.db['ratings']
        self.itemID_to_name = {}
        self.dataset = None
        self.trainset = None
        self.testset = None
        self.algo = None

    def load_data(self):
        # Fetch ratings data from MongoDB and convert it into a pandas DataFrame
        ratings_data = list(self.ratings_collection.find())
        ratings_df = pd.DataFrame(ratings_data)
        
        if not ratings_df.empty:
            ratings_df['user_id'] = ratings_df['user_id'].apply(lambda x: str(x))
            ratings_df['product_id'] = ratings_df['product_id'].apply(lambda x: str(x))
            ratings_df['rating'] = ratings_df['rating'].astype(int)
        
        # Debugging prints to check the integrity and distribution of the data
        print("Data loaded into DataFrame:")
        print(ratings_df.head())  # Shows the first few rows of the DataFrame
        print("\nData Description:")
        print(ratings_df.describe())  # Shows statistics for numerical columns
        print("\nNumber of unique users:", ratings_df['user_id'].nunique())  # Unique user count
        print("Number of unique products:", ratings_df['product_id'].nunique())  # Unique product count

        # Proceed to load data into Surprise
        data = Dataset.load_from_df(ratings_df[['user_id', 'product_id', 'rating']], Reader(rating_scale=(1, 5)))
        self.dataset = data.build_full_trainset()
        self.trainset = self.dataset
        self.testset = self.dataset.build_anti_testset()

        # Loading item names
        products_data = list(self.products_collection.find({}, {'_id': 0, 'product_id': 1, 'product_name': 1}))
        for product in products_data:
            self.itemID_to_name[str(product['product_id'])] = product['product_name']

        print("\nTrainset size:", self.trainset.n_ratings)
        print("Testset size:", len(self.testset))


    def train_model(self):
        sim_options = {'name': 'pearson_baseline', 'user_based': True}
        self.algo = KNNBasic(sim_options=sim_options)
        self.algo.fit(self.trainset)
        self.similarities = self.algo.compute_similarities()

    def get_recommendations(self, user_id):
        recommendations = []
        # Validate the UUID format to ensure it's correct
        try:
            UUID(user_id)  # This will raise a ValueError if user_id is not a valid UUID
        except ValueError:
            print(f"Invalid UUID format: {user_id}")
            return ["Invalid user ID format."]
        
        try:
            # Attempt to convert user ID to internal ID used by the trainset
            test_subject_iid = self.trainset.to_inner_uid(user_id)
            test_subject_ratings = self.trainset.ur[test_subject_iid]
            # Find all items that are not in the user's already-rated set
            all_items = set(self.trainset.all_items())
            rated_items = set(item for item, _ in test_subject_ratings)
            unrated_items = all_items - rated_items

            # Calculate the predicted rating for all unrated items
            candidates = []
            for itemID in unrated_items:
                predicted_rating = self.algo.predict(user_id, self.trainset.to_raw_iid(itemID)).est
                # Append the raw product_id directly, keeping the line to get item name as a comment
                candidates.append((self.trainset.to_raw_iid(itemID), predicted_rating))
                # item_name = self.get_item_name(self.trainset.to_raw_iid(itemID))  # This line fetches item name

            # Sort candidates by the predicted rating, highest first
            candidates.sort(key=lambda x: x[1], reverse=True)

            # Build the final list of recommendations
            for product_id, _ in candidates:
                recommendations.append(product_id)  # Append product_id to the recommendations list
                # if item_name:  # Optionally check for item name existence and use it
                #    recommendations.append(item_name)  # Commented out: originally appended item name

        except KeyError as e:
            print(f"KeyError - possibly incorrect user ID or item ID: {e}")
            return ["No recommendations available. User may not have rated enough items."]
        except IndexError as e:
            print(f"IndexError - accessed index is out of bounds: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        
        if not recommendations:
            recommendations = ["No recommendations available due to data inconsistency or input errors."]
        
        return recommendations




    def get_item_name(self, itemID):
        return self.itemID_to_name.get(itemID, "")

    def predict_ratings(self):
        predictions = self.algo.test(self.testset)
        return predictions

    def calculate_mse(self):
        predictions = self.algo.test(self.testset)
        mse = accuracy.mse(predictions, verbose=True)
        return mse

if __name__ == "__main__":
    db_uri = "mongodb+srv://admin:admin@cluster0.immhkre.mongodb.net/?retryWrites=true&w=majority"
    recommender = CollaFilterRecommender(db_uri, 'CollaFilter')
    recommender.load_data()
    recommender.train_model()
    mse = recommender.calculate_mse()
    print(f"Mean Squared Error: {mse}")
    user_uuid_str = '845355b8-23fd-44d7-a4f4-ac470e69db9e'
    recommendations = recommender.get_recommendations(user_uuid_str)
    for rec in recommendations:
        print("Recommended Item:", rec)