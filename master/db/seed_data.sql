INSERT INTO users
    (username, password_hash, role, first_name, last_name, phone, email, balance)
VALUES
    ('admin', 'scrypt:32768:8:1$YozR1MhLoev6JMPd$318c9114f9817fa4f142aa08bb8391af2a1c39c05d7c7b75a9bc9dfa8fd0973b8e9482ab2894a9223a58468cd66297d22d5a292c7e649b61df69b6b154b54515', 'admin', 'System', 'Admin', '0400000000', 'admin@scooter.local', 0.00),
    ('engineer1', 'scrypt:32768:8:1$tzaiRBRPcx4F6Lc7$d20f4ee5f88769dad3f50d909b6edffdfd1fb588671dba1bb62261d37ffc5ec4e44a9f1f10ff87c838e55c691e3072e7b29a75cfd0feee2dd237c216aa5a3dd5', 'engineer', 'Eva', 'Engineer', '0400000001', 'engineer1@scooter.local', 0.00),
    ('alice', 'scrypt:32768:8:1$irlrn5Bz5dTDISOe$598627b23cdf47b3cf7da1563386138e07c7c02592932f4f81d685bf7897fb751377d7370aba33b1f2811bcc82baf6d877816165f44fe988c1c1fe15b55cd252', 'customer', 'Alice', 'Nguyen', '0400000002', 'alice@example.com', 30.00),
    ('bob', 'scrypt:32768:8:1$uJ9jE6tMFF0qAQrX$f40b62dcbea9178539a5144115036f2e3e61149a3d729545f2315a150e37536b42152ea2ea57b7cbc960e07552add0d915aae71fda38023007b7e7b258d36ed7', 'customer', 'Bob', 'Tran', '0400000003', 'bob@example.com', 20.00)
ON DUPLICATE KEY UPDATE
    first_name = VALUES(first_name),
    last_name = VALUES(last_name),
    phone = VALUES(phone),
    balance = VALUES(balance);

INSERT INTO scooters
    (id, make, colour, location, latitude, longitude, cost_per_minute, status)
VALUES
    ('S001', 'Xiaomi', 'Black', 'Building 80', -37.8089000, 144.9633000, 0.50, 'Available'),
    ('S002', 'Segway', 'Red', 'Library', -37.8078000, 144.9630000, 0.60, 'Available')
ON DUPLICATE KEY UPDATE
    make = VALUES(make),
    colour = VALUES(colour),
    location = VALUES(location),
    latitude = VALUES(latitude),
    longitude = VALUES(longitude),
    cost_per_minute = VALUES(cost_per_minute),
    status = VALUES(status);
