import mysql.connector
from dotenv import load_dotenv
import os, uuid
from abc import ABC, abstractmethod
import sql_queries
import datetime as dt

load_dotenv(override=True)

HOST=os.getenv("DB_HOST")
USER=os.getenv("DB_USER")
PASSWORD=os.getenv("DB_PASSWORD")
DATABASE=os.getenv("DB_NAME")

class AbstractQueries(ABC):
    def __init__(self, connection=None):
        if connection is None:
            connection = mysql.connector.connect(
                host=HOST,
                user=USER,
                password=PASSWORD,
                database=DATABASE
            )
        self.connection = connection
        print("Succeed")

    def close(self):
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    @abstractmethod
    def create_table(self):
        pass

class UserAuthQueries(AbstractQueries):
    #1
    def create_table(self):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.USER_AUTH_CREATE_TABLE)
        self.connection.commit()
    #2
    def create_user(self, uid, username, password, created_at):
        values = (uid, username, password, created_at)

        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.USER_AUTH_INSERT, values)
        self.connection.commit()

        return cursor.rowcount == 1
    #3
    def get_user_by_id(self, auth_id):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.USER_AUTH_SELECT_BY_ID, (auth_id,))
            return cursor.fetchone()
    #4
    def get_user_by_username(self, username):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.USER_AUTH_SELECT_BY_USERNAME, (username,))
            return cursor.fetchone()
    #5
    def get_all_users(self):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.USER_AUTH_SELECT_ALL)
            return cursor.fetchall()
    #6
    def get_password_by_username(self, username):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.USER_AUTH_SELECT_PASS_BY_USERNAME, (username,))
            return cursor.fetchone()[0]
    #7
    def change_password(self, username, new_password):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.USER_AUTH_PASS_UPDATE, (new_password, username))
        self.connection.commit()
    #8
    def change_user_type(self, username, new_user_type):
        if new_user_type not in ('customer', 'admin', 'engineer'):
            raise ValueError("Invalid user type. Must be 'customer', 'admin', or 'engineer'.")

        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.USER_AUTH_TYPE_UPDATE, (new_user_type, username))
        self.connection.commit()
    #9
    def delete_user(self, auth_id):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.USER_AUTH_DELETE, (auth_id,))
        self.connection.commit()

class UserProfileQueries(AbstractQueries):
    #1
    def create_table(self):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.USER_PROFILE_CREATE_TABLE)
        self.connection.commit()
    #2
    def create_profile(self, user_id, first_name, last_name, phone_number, email, balance=0.00):
        values = (user_id, first_name, last_name, phone_number, email, balance)

        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.USER_PROFILE_INSERT, values)
        self.connection.commit()

        return cursor.rowcount == 1
    #3
    def get_profile_by_id(self, profile_id):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.USER_PROFILE_SELECT_BY_ID, (profile_id,))
            return cursor.fetchone()
    #4
    def get_all_profiles(self):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.USER_PROFILE_SELECT_ALL)
            return cursor.fetchall()
    #5
    def update_profile(self, profile_id, first_name, last_name, phone_number, email):
        values = (first_name, last_name, phone_number, email, profile_id)

        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.USER_PROFILE_UPDATE, values)
        self.connection.commit()
    #6
    def update_balance(self, profile_id, new_balance):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.USER_PROFILE_BALANCE_UPDATE, (new_balance, profile_id))
        self.connection.commit()
    #7
    def delete_profile(self, profile_id):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.USER_PROFILE_DELETE, (profile_id,))
        self.connection.commit()

class ScooterQueries(AbstractQueries):
    #1
    def create_table(self):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.SCOOTER_CREATE_TABLE)
        self.connection.commit()
    #2
    def create_scooter(self, color, brand, cost):
        values = (color, brand, cost)

        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.SCOOTER_INSERT, values)
        self.connection.commit()

        return cursor.rowcount == 1
    #3
    def get_scooter_by_id(self, scooter_id):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.SCOOTER_SELECT_BY_ID, (scooter_id,))
            return cursor.fetchone()
    #4
    def get_all_scooters(self):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.SCOOTER_SELECT_ALL)
            return cursor.fetchall()
    #5
    def change_scooter_info(self, scooter_id, color, brand, cost):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.SCOOTER_UPDATE_INFO_BY_ID, (color, brand, cost, scooter_id))
        self.connection.commit()
    #6
    def change_scooter_status(self, scooter_id, new_status):
        if new_status not in ('Available', 'Booked', 'Occupying', 'To Be Repaired', 'Under Repair'):
            raise ValueError("Invalid status. Must be 'Available', 'Booked', 'Occupying', 'To Be Repaired', or 'Under Repair'.")

        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.SCOOTER_UPDATE_STATUS_BY_ID, (new_status, scooter_id))
        self.connection.commit()
    #7
    def delete_scooter(self, scooter_id):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.SCOOTER_DELETE_BY_ID, (scooter_id,))
        self.connection.commit()

class RentalQueries(AbstractQueries):
    #1
    def create_table(self):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.RENTAL_CREATE_TABLE)
        self.connection.commit()
    #2
    def create_rental(self, user_id, scooter_id, start_time, end_time):
        values = (user_id, scooter_id, start_time, end_time)

        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.RENTAL_INSERT, values)
        self.connection.commit()

        return cursor.rowcount == 1
    #3
    def get_rental_by_id(self, rental_id):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.RENTAL_SELECT_BY_ID, (rental_id,))
            return cursor.fetchone()
    #4
    def get_rentals_by_customer_id(self, customer_id):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.RENTAL_SELECT_BY_CUSTOMER_ID, (customer_id,))
            return cursor.fetchall()
    #5
    def get_all_rentals(self):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.RENTAL_SELECT_ALL)
            return cursor.fetchall()
    #6
    def change_return_time(self, rental_id, new_return_time):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.RENTAL_UPDATE_RETURN_TIME_BY_ID, (new_return_time, rental_id))
        self.connection.commit()
    #7
    def delete_rental(self, rental_id):
        with self.connection.cursor() as cursor:
            cursor.execute(sql_queries.RENTAL_DELETE, (rental_id,))
        self.connection.commit()

if __name__ == "__main__":
    pass
