import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
from sklearn.decomposition import NMF



users_master = pd.read_csv('Users.csv', sep=';')
books_master = pd.read_csv('Books.csv', sep=';')
ratings_master = pd.read_csv('Ratings.csv', sep=';')

ratings = ratings_master.copy()

# Keep books with more than 20 ratings
book_rating_group = ratings.groupby(['ISBN']).count()
book_rating_group = book_rating_group[book_rating_group['Rating']>20]
ratings = ratings[ratings['ISBN'].isin(book_rating_group.index)]

# Keep users that have rated more than 3 books
user_rating_group = ratings.groupby(['User-ID']).count()
user_rating_group = user_rating_group[user_rating_group['Rating']>3]
ratings = ratings[ratings['User-ID'].isin(user_rating_group.index)]

# Apply to the books and users datasets
books = books_master.copy()
books = books[books['ISBN'].isin(ratings['ISBN'])]
users = users_master.copy()
users = users[users['User-ID'].isin(ratings['User-ID'])]

algo=svd()

cols = np.concatenate((['ISBN'],user_ids))
df = pd.DataFrame(columns=cols)
book_ids = books['ISBN']
df['ISBN'] = book_ids
df['ISBN'] = df['ISBN'].astype(str)

# Fill the df with the ratings from the Ratings.csv file
for i in range(ratings.shape[0]):
    user_id = ratings['User-ID'].iloc[i]
    book_id = ratings['ISBN'].iloc[i]
    rating = ratings['Rating'].iloc[i]
    row = df[df['ISBN']==book_id].index
    if len(row)>0:
        row = row[0]
        df.loc[row, user_id] = rating

df.columns = df.columns.astype(str)

# We will use this original_df later to verify whether or not a user has read a certain book
original_df = df.copy()
original_df = original_df.set_index('ISBN')
original_df.fillna('No Ranking', inplace=True)

# Replace NaN's with 0 to indicate books with no ratings
df.fillna(0,inplace=True)
df = df.set_index('ISBN')


def rank_calculation(data=df):
    """
    Calculate the optimal rank of the specified dataframe.
    """
    # Read the data
    df = data
    
    # Calculate benchmark value
    benchmark = np.linalg.norm(df, ord='fro') * 0.0001
    
    # Iterate through various values of rank to find optimal
    rank = 3
    while True:
        
        # initialize the model
        model = NMF(n_components=rank, init='random', random_state=0, max_iter=500)
        W = model.fit_transform(df)
        H = model.components_
        V = W @ H
        
        # Calculate RMSE of original df and new V
        RMSE = np.sqrt(mean_squared_error(df, V))
        
        if RMSE < benchmark:
            return rank, V
        
        # Increment rank if RMSE isn't smaller than the benchmark
        rank += 1

    return rank

# Hardcode the value so that we don't have to run the above function
#optimal_rank = rank_calculation()
optimal_rank = 15 


# Decompose the dataset using sklearn NMF
model = NMF(n_components=optimal_rank)
model.fit(df)

H = pd.DataFrame(model.components_)    
W = pd.DataFrame(model.transform(df))    
V = pd.DataFrame(np.dot(W,H), columns=df.columns)
V.index = df.index
V


user_id = '276521'
# Grab top 10 books ID's that the user hasn't reviewed
user_col = V[user_id]
user_col = user_col.sort_values(ascending=False)

top_10_ISBN = []
for book in user_col.index:
    if original_df[user_id].loc[book] == 'No Ranking': # haven't read the book
        top_10_ISBN.append(book)

    if len(top_10_ISBN) == 10:
        break

top_10_ISBN


# Return the titles and authors of the recommended books
books_df = books.set_index('ISBN')
books_df.index = books_df.index.astype(str)

top_10_books = []
for book in top_10_ISBN:
    top_10_books.append([books_df['Title'].loc[book], books_df['Author'].loc[book]])

top_10_books = pd.DataFrame(top_10_books, columns=['Title','Author'])

print(f'Top 10 Book Recommendations for user {user_id}:')
top_10_books