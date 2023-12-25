import firebase_admin
from loguru import logger
from firebase_admin import credentials, db


class FirebaseRealtimeDatabase:
    def __init__(self, database_url: str, service_account_key_path: str):
        cred = credentials.Certificate(service_account_key_path)
        firebase_admin.initialize_app(cred, {"databaseURL": database_url})
        self.__db_ref = db.reference()

    def set_ref(self, path):
        self.__db_ref = self.__db_ref.child(path)
        return self

    def delete_data(self, path):
        """
        Delete data from the specified path in the Firebase Realtime Database.

        Args:
            path (str): The path from which to delete the data.

        Returns:
            bool: True if the data is successfully deleted, False otherwise.
        """
        try:
            self.__db_ref.child(path).delete()
            return True
        except Exception as e:
            print(f"Error deleting data: {e}")
            return False

    def put_data(self, path, data):
        """
        Put data into the specified path in the Firebase Realtime Database.

        Args:
            path (str): The path to store the data in the database.
            data (dict): The data to be stored as a dictionary.

        Returns:
            bool: True if the data is successfully stored, False otherwise.
        """
        try:
            self.__db_ref.child(path).set(data)
            return True
        except Exception as e:
            logger.error(f"Error putting data: {e}")
            return False

    def get_data(self, path):
        """
        Get data from the specified path in the Firebase Realtime Database.

        Args:
            path (str): The path to the data in the database.

        Returns:
            dict: The retrieved data as a dictionary.
        """
        try:
            data = self.__db_ref.child(path).get()
            return data
        except Exception as e:
            logger.error(f"Error getting data: {e}")
            return None

    def query_data(self, path, query):
        """
        Query data from the specified path in the Firebase Realtime Database.

        Args:
            path (str): The path to the data in the database.
            query (str): The query string.

        Returns:
            dict: The queried data as a dictionary.
        """
        try:
            data = self.__db_ref.child(path).order_by_child(query).get()
            return data
        except Exception as e:
            logger.error(f"Error querying data: {e}")
            return None
