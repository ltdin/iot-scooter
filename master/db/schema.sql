CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'customer', 'engineer') NOT NULL,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    phone VARCHAR(30) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    balance DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scooters (
    id VARCHAR(20) PRIMARY KEY,
    make VARCHAR(80) NOT NULL,
    colour VARCHAR(40) NOT NULL,
    location VARCHAR(120) NOT NULL,
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    cost_per_minute DECIMAL(10, 2) NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'Available',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    scooter_id VARCHAR(20) NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'Active',
    booked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    unlock_time DATETIME NULL,
    lock_time DATETIME NULL,
    calendar_event_id VARCHAR(255) NULL,
    CONSTRAINT fk_bookings_user
        FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_bookings_scooter
        FOREIGN KEY (scooter_id) REFERENCES scooters(id)
);

CREATE TABLE IF NOT EXISTS reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scooter_id VARCHAR(20) NOT NULL,
    reported_by INT NOT NULL,
    issue_description TEXT NOT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'Open',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME NULL,
    CONSTRAINT fk_reports_scooter
        FOREIGN KEY (scooter_id) REFERENCES scooters(id),
    CONSTRAINT fk_reports_user
        FOREIGN KEY (reported_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS usage_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    scooter_id VARCHAR(20) NOT NULL,
    booking_id INT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    duration_minutes INT NOT NULL,
    total_cost DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usage_user
        FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_usage_scooter
        FOREIGN KEY (scooter_id) REFERENCES scooters(id),
    CONSTRAINT fk_usage_booking
        FOREIGN KEY (booking_id) REFERENCES bookings(id)
);

CREATE TABLE IF NOT EXISTS repair_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    engineer_id INT NOT NULL,
    scooter_id VARCHAR(20) NOT NULL,
    report_id INT NULL,
    result TEXT NOT NULL,
    repaired_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_repair_engineer
        FOREIGN KEY (engineer_id) REFERENCES users(id),
    CONSTRAINT fk_repair_scooter
        FOREIGN KEY (scooter_id) REFERENCES scooters(id),
    CONSTRAINT fk_repair_report
        FOREIGN KEY (report_id) REFERENCES reports(id)
);
