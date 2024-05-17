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
        self.ratings_collection = self.db['ratings']
        self.dataset = None
        self.trainset = None
        self.testset = None
        self.algo = None
        self.similarities = None  # Initialize similarities here

    def load_data(self):
        ratings_data = list(self.ratings_collection.find())
        ratings_df = pd.DataFrame(ratings_data)
        if not ratings_df.empty:
            ratings_df['user_id'] = ratings_df['user_id'].apply(lambda x: str(x))
            ratings_df['product_id'] = ratings_df['product_id'].apply(lambda x: str(x))
            ratings_df['rating'] = ratings_df['rating'].astype(int)
        data = Dataset.load_from_df(ratings_df[['user_id', 'product_id', 'rating']], Reader(rating_scale=(1, 5)))
        self.dataset = data.build_full_trainset()
        self.trainset = self.dataset
        self.testset = self.dataset.build_anti_testset()

    def train_model(self):
        sim_options = {'name': 'pearson_baseline', 'user_based': True}
        self.algo = KNNBasic(sim_options=sim_options)
        self.algo.fit(self.trainset)
        self.similarities = self.algo.compute_similarities()
        print("Model trained and similarities computed successfully.")

    def get_recommendations(self, user_id, top_n=75):
        recommendations = []
        try:
            UUID(user_id)  # Validate UUID format
        except ValueError:
            print(f"Invalid UUID format: {user_id}")
            return ["Invalid user ID format."]
        
        try:
            user_inner_id = self.trainset.to_inner_uid(user_id)
        except ValueError:
            # Fallback for users not found in trainset
            all_products = list(set([self.trainset.to_raw_iid(i) for i in self.trainset.all_items()]))
            recommendations = random.sample(all_products, min(len(all_products), top_n))
            print(f"User not found in ratings. Generating random recommendations for {user_id}")
            return recommendations

        # Get the top-N neighbors for the user
        neighbors = []
        for other in self.trainset.all_users():
            if other != user_inner_id:
                distance = self.algo.sim[user_inner_id, other]
                neighbors.append((other, distance))
        
        # Sort neighbors by similarity
        neighbors = sorted(neighbors, key=lambda x: x[1], reverse=True)[:top_n]

        # Compute weighted sum of ratings from neighbors
        candidates = defaultdict(float)
        for neighbor, score in neighbors:
            for itemID, rating in self.trainset.ur[neighbor]:
                candidates[itemID] += score * (rating / 5.0)

        # Filter items user has already rated
        watched = {itemID for itemID, _ in self.trainset.ur[user_inner_id]}
        sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
        for itemID, score in sorted_candidates:
            if itemID not in watched:
                raw_item_id = self.trainset.to_raw_iid(itemID)
                recommendations.append(raw_item_id)
                if len(recommendations) >= top_n:
                    break
        
        return recommendations


    def get_additional_recommendations(self, user_id, top_n=10):
        # Retrieve the initial recommendations to exclude them
        initial_recommendations = self.get_recommendations(user_id, 75)

        # Fetch all possible products
        all_products = list(set([self.trainset.to_raw_iid(i) for i in self.trainset.all_items()]))

        # Exclude the initial recommendations
        additional_candidates = [item for item in all_products if item not in initial_recommendations]

        # Generate additional recommendations
        additional_recommendations = random.sample(additional_candidates, min(len(additional_candidates), top_n))

        return additional_recommendations

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
    user_uuid_str = '706d8e81-7430-4c43-b797-67510ea05892'
    recommendations = recommender.get_recommendations(user_uuid_str)
    for rec in recommendations:
        print("Recommended Item:", rec)

