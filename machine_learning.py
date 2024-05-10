import pandas as pd
from surprise import KNNBasic, Dataset, Reader, accuracy
from collections import defaultdict
from operator import itemgetter
import heapq
from pymongo import MongoClient
from uuid import UUID
import random

client = MongoClient("mongodb+srv://admin:admin@cluster0.immhkre.mongodb.net/CollaFilter")

def CollaFilterRecommender(user_id):
    print(user_id)
    db = client["CollaFilter"]
    products_collection = db['products']
    ratings_collection = db['ratings']
    itemID_to_name = {}
    dataset = None
    trainset = None
    testset = None
    algo = None

    def load_data():
        # Fetch ratings data from MongoDB and convert it into a pandas DataFrame
        ratings_data = list(ratings_collection.find())
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
        nonlocal dataset, trainset, testset
        dataset = data.build_full_trainset()
        trainset = dataset
        testset = dataset.build_anti_testset()

        # Loading item names
        products_data = list(products_collection.find({}, {'_id': 0, 'product_id': 1, 'name': 1}))
        for product in products_data:
            itemID_to_name[str(product['product_id'])] = product['name']

        print("\nTrainset size:", trainset.n_ratings)
        print("Testset size:", len(testset))

    def train_model():
        nonlocal algo
        sim_options = {'name': 'pearson_baseline', 'user_based': True}
        algo = KNNBasic(sim_options=sim_options)
        algo.fit(trainset)

    def get_recommendations(user_id, max_recommendations):
        recommendations = []
        try:
            UUID(user_id)  # Validate UUID format
        except ValueError:
            print(f"Invalid UUID format: {user_id}")
            return ["Invalid user ID format."]

        try:
            # Convert user ID to internal ID
            test_subject_iid = trainset.to_inner_uid(user_id)
            test_subject_ratings = trainset.ur[test_subject_iid]

            # Find all unrated items
            all_items = set(trainset.all_items())
            rated_items = set(item for item, _ in test_subject_ratings)
            unrated_items = all_items - rated_items

            # Calculate the predicted rating for all unrated items
            candidates = []
            for itemID in unrated_items:
                predicted_rating = algo.predict(user_id, trainset.to_raw_iid(itemID)).est
                candidates.append((trainset.to_raw_iid(itemID), predicted_rating))

            # Sort candidates by predicted rating, highest first
            candidates.sort(key=lambda x: x[1], reverse=True)

            # Build the final list of recommendations
            for product_id, _ in candidates:
                recommendations.append(product_id)
                if max_recommendations is not None and len(recommendations) >= max_recommendations:
                    break

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

    def get_item_name(itemID):
        return itemID_to_name.get(itemID, "")

    def predict_ratings():
        predictions = algo.test(testset)
        return predictions

    def calculate_mse():
        predictions = algo.test(testset)
        mse = accuracy.mse(predictions, verbose=True)
        return mse

    load_data()
    train_model()
    mse = calculate_mse()
    print(f"Mean Squared Error: {mse}")
    # user_uuid_str = 'bda1f53c-72cb-4da1-a715-bb7f779a9ba1'
    recommendations = get_recommendations(user_id, max_recommendations=None)
    for rec in recommendations:
        print("Recommended Item:", rec)

if __name__ == "__main__":
    db_uri = "mongodb+srv://admin:admin@cluster0.immhkre.mongodb.net/?retryWrites=true&w=majority"
    CollaFilterRecommender(db_uri, 'CollaFilter')
