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

    def load_data(self):
        ratings_data = list(self.ratings_collection.find())
        ratings_df = pd.DataFrame(ratings_data)

        if not ratings_df.empty:
            ratings_df['user_id'] = ratings_df['user_id'].apply(lambda x: str(x))
            ratings_df['product_id'] = ratings_df['product_id'].apply(lambda x: str(x))
            ratings_df['rating'] = ratings_df['rating'].astype(int)

        print("Data loaded into DataFrame:")
        print(ratings_df.head())
        print("\nData Description:")
        print(ratings_df.describe())
        print("\nNumber of unique users:", ratings_df['user_id'].nunique())
        print("Number of unique products:", ratings_df['product_id'].nunique())

        data = Dataset.load_from_df(ratings_df[['user_id', 'product_id', 'rating']], Reader(rating_scale=(1, 5)))
        self.dataset = data.build_full_trainset()
        self.trainset = self.dataset
        self.testset = self.dataset.build_anti_testset()

    def train_model(self):
        sim_options = {'name': 'pearson_baseline', 'user_based': True}
        self.algo = KNNBasic(sim_options=sim_options)
        self.algo.fit(self.trainset)
        self.similarities = self.algo.compute_similarities()

    def get_recommendations(self, user_id, top_n=1000):
        recommendations = []
        try:
            UUID(user_id)  # Validate UUID format
        except ValueError:
            print(f"Invalid UUID format: {user_id}")
            return ["Invalid user ID format."]
        
        try:
            test_subject_iid = self.trainset.to_inner_uid(user_id)
            test_subject_ratings = self.trainset.ur[test_subject_iid]
            k_neighbours = heapq.nlargest(top_n, test_subject_ratings, key=lambda t: t[1])

            candidates = defaultdict(float)
            for itemID, rating in k_neighbours:
                if itemID < len(self.similarities):
                    similarities = self.similarities[itemID]
                    for innerID, score in enumerate(similarities):
                        if innerID < len(self.similarities):
                            candidates[innerID] += score * (rating / 5.0)

            watched = {itemID for itemID, _ in self.trainset.ur[test_subject_iid]}
            sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
            top_candidates = sorted_candidates[:top_n * 3]

            selected_items = random.sample(top_candidates, min(len(top_candidates), top_n))
            for itemID, _ in selected_items:
                if itemID not in watched:
                    raw_item_id = self.trainset.to_raw_iid(itemID)
                    recommendations.append(raw_item_id)
                    if len(recommendations) >= top_n:
                        break
        except Exception as e:
            print(f"Unexpected error: {e}")
            recommendations = ["No recommendations available due to data inconsistency or input errors."]
        
        return recommendations

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
    user_uuid_str = '73f75fda-0d30-489c-99ca-e97e0ff3104e'
    recommendations = recommender.get_recommendations(user_uuid_str)
    for rec in recommendations:
        print("Recommended Item:", rec)