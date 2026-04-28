CREATE TABLE PENGGUNA (
    email VARCHAR(100) PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    salutation VARCHAR(10) NOT NULL,
    first_mid_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    country_code VARCHAR(5) NOT NULL,
    mobile_number VARCHAR(20) NOT NULL,
    tanggal_lahir DATE NOT NULL,
    kewarganegaraan VARCHAR(50) NOT NULL
);

CREATE TABLE TIER (
    id_tier VARCHAR(10) PRIMARY KEY,
    nama VARCHAR(50) NOT NULL,
    minimal_frekuensi_terbang INT NOT NULL,
    minimal_tier_miles INT NOT NULL
);

CREATE SEQUENCE member_seq START 1;

CREATE TABLE MEMBER (
    email VARCHAR(100) PRIMARY KEY,
    nomor_member VARCHAR(20) NOT NULL UNIQUE DEFAULT (
        'M' || LPAD(nextval('member_seq')::TEXT, 4, '0')
    ),
    tanggal_bergabung DATE NOT NULL,
    id_tier VARCHAR(10) NOT NULL,
    award_miles INT DEFAULT 0,
    total_miles INT DEFAULT 0,
    FOREIGN KEY (email) REFERENCES PENGGUNA(email) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (id_tier) REFERENCES TIER(id_tier)
);

CREATE TABLE PENYEDIA (
    id SERIAL PRIMARY KEY
);

CREATE TABLE MASKAPAI (
    kode_maskapai VARCHAR(10) PRIMARY KEY,
    nama_maskapai VARCHAR(100) NOT NULL,
    id_penyedia INT NOT NULL,
    FOREIGN KEY (id_penyedia) REFERENCES PENYEDIA(id)
);

CREATE TABLE BANDARA (
    iata_code CHAR(3) PRIMARY KEY,
    nama VARCHAR(100) NOT NULL,
    kota VARCHAR(100) NOT NULL,
    negara VARCHAR(100) NOT NULL
);

CREATE TABLE MITRA (
    email_mitra VARCHAR(100) PRIMARY KEY,
    id_penyedia INT NOT NULL UNIQUE,
    nama_mitra VARCHAR(100) NOT NULL,
    tanggal_kerja_sama DATE NOT NULL,
    FOREIGN KEY (id_penyedia) REFERENCES PENYEDIA(id) ON DELETE CASCADE
);

CREATE SEQUENCE hadiah_seq START 1;

CREATE TABLE HADIAH (
    kode_hadiah VARCHAR(20) PRIMARY KEY DEFAULT ('RWD-' || LPAD(nextval('hadiah_seq')::TEXT, 3, '0')),
    nama VARCHAR(100) NOT NULL,
    miles INT NOT NULL,
    deskripsi TEXT,
    valid_start_date DATE NOT NULL,
    program_end DATE NOT NULL,
    id_penyedia INT NOT NULL,
    FOREIGN KEY (id_penyedia) REFERENCES PENYEDIA(id) ON DELETE CASCADE
);