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

CREATE SEQUENCE staf_seq START 1;

CREATE TABLE STAF (
    email VARCHAR(100) PRIMARY KEY,
    id_staf VARCHAR(20) NOT NULL UNIQUE DEFAULT (
        'S' || LPAD(nextval('staf_seq')::TEXT, 4, '0')
    ),
    kode_maskapai VARCHAR(10) NOT NULL,
    FOREIGN KEY (email) REFERENCES PENGGUNA(email) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (kode_maskapai) REFERENCES MASKAPAI(kode_maskapai)
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

CREATE TABLE IDENTITAS (
    nomor VARCHAR(50) PRIMARY KEY,
    email_member VARCHAR(100) NOT NULL,
    tanggal_habis DATE NOT NULL,
    tanggal_terbit DATE NOT NULL CHECK (tanggal_habis > tanggal_terbit),
    negara_penerbit VARCHAR(50) NOT NULL,
    jenis VARCHAR(30) NOT NULL CHECK (jenis IN ('Paspor', 'KTP', 'SIM')),
    FOREIGN KEY (email_member) REFERENCES MEMBER(email) ON DELETE CASCADE
);

CREATE TABLE CLAIM_MISSING_MILES (
    id SERIAL PRIMARY KEY,
    email_member VARCHAR(100) NOT NULL,
    email_staf VARCHAR(100), 
    maskapai VARCHAR(10) NOT NULL,
    bandara_asal VARCHAR(3) NOT NULL,
    bandara_tujuan VARCHAR(3) NOT NULL,
    tanggal_penerbangan DATE NOT NULL,
    flight_number VARCHAR(10) NOT NULL,
    nomor_tiket VARCHAR(20) NOT NULL,
    kelas_kabin varchar(20) NOT NULL CHECK (kelas_kabin IN ('Economy', 'Business', 'First')),
    pnr VARCHAR(10) NOT NULL,
    status_penerimaan VARCHAR(20) NOT NULL DEFAULT 'Menunggu' CHECK (status_penerimaan IN ('Menunggu', 'Disetujui', 'Ditolak')),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    FOREIGN KEY (email_member) REFERENCES MEMBER(email) ON DELETE CASCADE,
    FOREIGN KEY (email_staf) REFERENCES STAF(email),
    FOREIGN KEY (maskapai) REFERENCES MASKAPAI(kode_maskapai),
    FOREIGN KEY (bandara_asal) REFERENCES BANDARA(iata_code),
    FOREIGN KEY (bandara_tujuan) REFERENCES BANDARA(iata_code),
    UNIQUE (email_member, flight_number, tanggal_penerbangan, nomor_tiket);
)

CREATE SEQUENCE seq_amp START 1;

CREATE TABLE AWARD_MILES_PACKAGE (
    id VARCHAR(20) PRIMARY KEY DEFAULT 'AMP-' || LPAD(nextval('seq_amp')::TEXT, 3, '0'),
    harga_paket DECIMAL(15, 2) NOT NULL CHECK (harga_paket > 0),
    jumlah_award_miles INT NOT NULL CHECK (jumlah_award_miles > 0),
);

CREATE TABLE MEMBER_AWARD_MILES_PACKAGE (
    id_award_miles_package VARCHAR(20) NOT NULL,
    email_member VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id_award_miles_package, email_member, timestamp),
    FOREIGN KEY (id_award_miles_package) REFERENCES AWARD_MILES_PACKAGE(id),
    FOREIGN KEY (email_member) REFERENCES MEMBER(email) ON DELETE CASCADE
);

CREATE TABLE TRANSFER (
    email_member_1 VARCHAR(100) NOT NULL,
    email_member_2 VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    jumlah INT NOT NULL CHECK (jumlah > 0),
    catatan VARCHAR(255),
    PRIMARY KEY (email_member_1, email_member_2, timestamp),
    FOREIGN KEY (email_member_1) REFERENCES MEMBER(email) ON DELETE CASCADE,
    FOREIGN KEY (email_member_2) REFERENCES MEMBER(email) ON DELETE CASCADE,
    CHECK (email_member_1 <> email_member_2)
);

CREATE TABLE REDEEM (
    email_member VARCHAR(100) NOT NULL,
    kode_hadiah VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (email_member, kode_hadiah, timestamp),
    FOREIGN KEY (email_member) REFERENCES MEMBER(email) ON DELETE CASCADE,
    FOREIGN KEY (kode_hadiah) REFERENCES HADIAH(kode_hadiah)
);