import sys
import os
from pymongo import MongoClient

def test_connection(uri):
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.server_info()
        print('Connected successfully')
        return 0
    except Exception as e:
        print(f'Error: {e}')
        return 1

def clean_database(uri):
    try:
        client = MongoClient(uri)
        db = client.get_database()
        collections = db.list_collection_names()
        for col in collections:
            db[col].delete_many({})
            print(f'Cleared collection: {col}')
        print('Database cleaned successfully')
        return 0
    except Exception as e:
        print(f'Error: {e}')
        return 1

def show_stats(uri):
    try:
        client = MongoClient(uri)
        db = client.get_database()
        collections = sorted(db.list_collection_names())
        
        print('')
        print('Collections:')
        print('-' * 50)
        
        if collections:
            total = 0
            for col in collections:
                count = db[col].count_documents({})
                print(f'{col}: {count} documents')
                total += count
            print('-' * 50)
            print(f'Total documents: {total}')
        else:
            print('No collections found')
        
        return 0
    except Exception as e:
        print(f'Error: {e}')
        return 1

if __name__ == '__main__':
    # Get URI from environment variable to avoid command-line parsing issues
    uri = os.environ.get('MONGO_URI_PARAM')
    
    if not uri:
        print('Error: MONGO_URI_PARAM environment variable not set')
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print('Usage: mongo_helper.py <command>')
        print('Commands: test, clean, stats')
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'test':
        sys.exit(test_connection(uri))
    elif command == 'clean':
        sys.exit(clean_database(uri))
    elif command == 'stats':
        sys.exit(show_stats(uri))
    else:
        print(f'Unknown command: {command}')
        sys.exit(1)
