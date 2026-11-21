#################################################################
# TABLE: user_auth
#1
USER_AUTH_CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS user_auth (
        auth_id         CHAR(36) PRIMARY KEY,
        username        VARCHAR(50) NOT NULL UNIQUE,
        password        VARCHAR(255) NOT NULL,
        user_type       ENUM('customer', 'admin', 'engineer') DEFAULT 'customer' NOT NULL,
        created_at      TEXT NOT NULL
    )
"""
#2
USER_AUTH_INSERT = """
    INSERT INTO user_auth (auth_id, username, password, created_at) 
    VALUES (%s, %s, %s, %s)
"""
#3
USER_AUTH_SELECT_BY_ID = """
    SELECT username, user_type, created_at
    FROM user_auth WHERE auth_id=%s
"""
#4
USER_AUTH_SELECT_BY_USERNAME = """
    SELECT username, user_type, created_at
    FROM user_auth WHERE username=%s
"""
#5
USER_AUTH_SELECT_PASS_BY_USERNAME = """
    SELECT password 
    FROM user_auth WHERE username=%s
"""
#6
USER_AUTH_SELECT_ALL = """
    SELECT auth_id, username, user_type, created_at
    FROM user_auth
"""
#7
USER_AUTH_PASS_UPDATE = """
    UPDATE user_auth SET password=%s WHERE username=%s
"""
#8
USER_AUTH_TYPE_UPDATE = """
    UPDATE user_auth SET user_type=%s WHERE username=%s
"""
#9
USER_AUTH_DELETE = """
    DELETE FROM user_auth WHERE auth_id=%s
"""
#################################################################

#################################################################
# TABLE: user_profile
#1
USER_PROFILE_CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS user_profile (
        profile_id      CHAR(36) PRIMARY KEY,
        first_name      VARCHAR(50) NOT NULL,
        last_name       VARCHAR(50) NOT NULL,
        phone_number    VARCHAR(20) NOT NULL,
        email           VARCHAR(100) NOT NULL UNIQUE,
        balance         DECIMAL(10, 2) NOT NULL DEFAULT 0.00,

        FOREIGN KEY (profile_id) REFERENCES user_auth(auth_id) ON DELETE CASCADE
    )
"""
#2
USER_PROFILE_INSERT = """
    INSERT INTO user_profile (profile_id, first_name, last_name, phone_number, email, balance) 
    VALUES (%s, %s, %s, %s, %s, %s)
"""
#3
USER_PROFILE_SELECT_BY_ID = """
    SELECT first_name, last_name, phone_number, email, balance
    FROM user_profile WHERE profile_id=%s
"""
#4
USER_PROFILE_SELECT_ALL = """
    SELECT profile_id, first_name, last_name, phone_number, email, balance
    FROM user_profile
"""
#5
USER_PROFILE_UPDATE_BY_ID = """
    UPDATE user_profile 
    SET first_name=%s, last_name=%s, phone_number=%s, email=%s
    WHERE profile_id=%s
"""
#6
USER_PROFILE_BALANCE_UPDATE_BY_ID = """
    UPDATE user_profile 
    SET balance=%s
    WHERE profile_id=%s
"""
#7
USER_PROFILE_DELETE_BY_ID = """
    DELETE FROM user_profile WHERE profile_id=%s
"""
#################################################################

#################################################################
# TABLE: scooters
#1
SCOOTER_CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS scooters (
        scooter_id      INT PRIMARY KEY AUTO_INCREMENT,
        color           VARCHAR(30) NOT NULL,
        brand           VARCHAR(50) NOT NULL,
        cost            DECIMAL(10, 2) NOT NULL,
        status          ENUM('Available', 'Booked', 'Occupying', 'To Be Repaired', 'Under Repair') DEFAULT 'Available' NOT NULL
    )
"""
#2
SCOOTER_INSERT = """
    INSERT INTO scooters (color, brand, cost) 
    VALUES (%s, %s, %s)
"""
#3
SCOOTER_SELECT_BY_ID = """
    SELECT color, brand, cost, status
    FROM scooters WHERE scooter_id=%s
"""
#4
SCOOTER_SELECT_ALL = """
    SELECT scooter_id, color, brand, cost, status
    FROM scooters
"""
#5
SCOOTER_UPDATE_INFO_BY_ID = """
    UPDATE scooters 
    SET color=%s, brand=%s, cost=%s
    WHERE scooter_id=%s
"""
#6
SCOOTER_UPDATE_STATUS_BY_ID = """
    UPDATE scooters 
    SET status=%s
    WHERE scooter_id=%s
"""
#7
SCOOTER_DELETE_BY_ID = """
    DELETE FROM scooters WHERE scooter_id=%s
"""
#################################################################

#################################################################
# TABLE: rentals
#1
RENTAL_CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS rentals (
        rental_id       INT PRIMARY KEY AUTO_INCREMENT,
        scooter_id      CHAR(36) NOT NULL,
        customer_id     CHAR(36) NOT NULL,
        rent_time       TEXT NOT NULL,
        return_time     TEXT NOT NULL,

        FOREIGN KEY (scooter_id) REFERENCES scooters(scooter_id),
        FOREIGN KEY (customer_id) REFERENCES auth(auth_id)
    )
"""
#2
RENTAL_INSERT = """
    INSERT INTO rentals (scooter_id, customer_id, rent_time, return_time)
    VALUES (%s, %s, %s, %s)
"""
#3
RENTAL_SELECT_BY_ID = """
    SELECT scooter_id, customer_id, rent_time, return_time
    FROM rentals WHERE rental_id=%s
"""
#4
RENTAL_SELECT_BY_CUSTOMER_ID = """
    SELECT rental_id, scooter_id, rent_time, return_time
    FROM rentals WHERE customer_id=%s
"""
#5
RENTAL_SELECT_ALL = """
    SELECT rental_id, scooter_id, customer_id, rent_time, return_time
    FROM rentals
"""
#6
RENTAL_UPDATE_RETURN_TIME_BY_ID = """
    UPDATE rentals 
    SET return_time=%s
    WHERE rental_id=%s
"""
#7
RENTAL_DELETE_BY_ID = """
    DELETE FROM rentals WHERE rental_id=%s
"""
#################################################################