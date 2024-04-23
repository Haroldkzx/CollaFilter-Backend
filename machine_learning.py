import pandas as pd
import csv
from surprise import KNNBasic, Dataset, Reader, accuracy
from collections import defaultdict
from operator import itemgetter
import heapq

class CollaFilterRecommender:
    def __init__(self, ratings_file, items_file):
        self.ratings_file = ratings_file
        self.items_file = items_file
        self.itemID_to_name = {}
        self.itemID_to_newID = {}
        self.newID_to_itemID = {}
        self.dataset = None
        self.trainset = None
        self.testset = None
        self.algo = None

    def load_data(self):
        reader = Reader(line_format='user item rating timestamp', sep=',', skip_lines=1)
        # Load the dataset
        data = Dataset.load_from_file(self.ratings_file, reader=reader)
        self.dataset = data.build_full_trainset()
        self.trainset = self.dataset
        self.testset = self.dataset.build_anti_testset()

        # Load item data and create mapping
        new_item_id = 0
        with open(self.items_file, newline='', encoding='ISO-8859-1') as csvfile:
            item_reader = csv.reader(csvfile)
            next(item_reader)  # Skip header
            for row in item_reader:
                original_itemID, item_name = row[0], row[1]
                if original_itemID not in self.itemID_to_newID:
                    self.itemID_to_newID[original_itemID] = new_item_id
                    self.newID_to_itemID[new_item_id] = original_itemID
                    self.itemID_to_name[original_itemID] = item_name
                    new_item_id += 1

        print("Trainset size:", self.trainset.n_ratings)
        print("Testset size:", len(self.testset))

    def train_model(self):
        sim_options = {
            'name': 'pearson_baseline',
            'user_based': True
        }
        self.algo = KNNBasic(sim_options=sim_options)
        self.algo.fit(self.trainset)

    def get_recommendations(self, user_id, top_n=10):
        recommendations = []
        try:
            test_subject_iid = self.trainset.to_inner_uid(str(user_id))
            test_subject_ratings = self.trainset.ur[test_subject_iid]
            k_neighbours = heapq.nlargest(top_n, test_subject_ratings, key=lambda t: t[1])

            candidates = defaultdict(float)
            # Ensure we only compute similarities once for efficiency
            all_similarities = self.algo.compute_similarities()

            for itemID, rating in k_neighbours:
                if itemID < len(all_similarities):  # Check if the itemID index is valid within the similarity matrix
                    similarities = all_similarities[itemID]
                    for innerID, score in enumerate(similarities):
                        if innerID < len(all_similarities):  # Additional check for valid indices
                            candidates[innerID] += score * (rating / 5.0)

            watched = {itemID for itemID, _ in self.trainset.ur[test_subject_iid]}
            for itemID, rating_sum in sorted(candidates.items(), key=itemgetter(1), reverse=True):
                if itemID not in watched:
                    raw_item_id = self.newID_to_itemID.get(itemID)  # Ensure this mapping exists
                    if raw_item_id is not None:
                        item_name = self.get_item_name(raw_item_id)
                        if item_name:
                            recommendations.append(item_name)
                            if len(recommendations) >= top_n:
                                break
        except KeyError as e:
            print(f"KeyError - possibly incorrect user ID or item ID: {e}")
        except IndexError as e:
            print(f"IndexError - accessed index is out of bounds: {e}")

        if not recommendations:
            recommendations = ["No recommendations available due to data inconsistency or input errors."]

        return recommendations


    def get_item_name(self, itemID):
        return self.itemID_to_name.get(str(itemID), "")

    def predict_ratings(self):
        predictions = self.algo.test(self.testset)
        return predictions

    def calculate_mse(self):
        predictions = self.algo.test(self.testset)
        mse = accuracy.mse(predictions, verbose=True)
        return mse

if __name__ == "__main__":
    recommender = CollaFilterRecommender('collaFilter-sample-data/ratings.csv', 'collaFilter-sample-data/items.csv')
    recommender.load_data()
    recommender.train_model()
    mse = recommender.calculate_mse()
    print(f"Mean Squared Error: {mse}")
    recommendations = recommender.get_recommendations('30')
    for rec in recommendations:
        print("Recommended Item:", rec)