INSERT INTO PENYEDIA (id) VALUES
  (1), (2), (3), (4), (5), (6), (7), (8);

INSERT INTO MASKAPAI (kode_maskapai, nama_maskapai, id_penyedia) VALUES
  ('GA', 'Garuda Indonesia', 1),
  ('QG', 'Citilink Indonesia', 2),
  ('JT', 'Lion Air', 3),
  ('SJ', 'Sriwijaya Air', 4),
  ('ID', 'Batik Air', 5);

INSERT INTO BANDARA (iata_code, nama, kota, negara) VALUES
  ('CGK', 'Soekarno-Hatta International Airport', 'Tangerang', 'Indonesia'),
  ('DPS', 'Ngurah Rai International Airport', 'Denpasar', 'Indonesia'),
  ('SUB', 'Juanda International Airport', 'Surabaya', 'Indonesia'),
  ('SIN', 'Singapore Changi Airport', 'Singapore', 'Singapore'),
  ('KUL', 'Kuala Lumpur International Airport', 'Kuala Lumpur', 'Malaysia'),
  ('BKK', 'Suvarnabhumi Airport', 'Bangkok', 'Thailand'),
  ('HKG', 'Hong Kong International Airport', 'Hong Kong', 'China'),
  ('NRT', 'Narita International Airport', 'Tokyo', 'Japan'),
  ('ICN', 'Incheon International Airport', 'Seoul', 'South Korea'),
  ('SYD', 'Sydney Kingsford Smith Airport', 'Sydney', 'Australia'),
  ('DXB', 'Dubai International Airport', 'Dubai', 'UAE'),
  ('LHR', 'Heathrow Airport', 'London', 'United Kingdom'),
  ('CDG', 'Charles de Gaulle Airport', 'Paris', 'France'),
  ('AMS', 'Amsterdam Airport Schiphol', 'Amsterdam', 'Netherlands'),
  ('LAX', 'Los Angeles International Airport', 'Los Angeles', 'USA');

INSERT INTO MITRA (email_mitra, id_penyedia, nama_mitra, tanggal_kerja_sama) VALUES
  ('mitra@garuda.com', 1, 'Garuda Miles Partner', '2020-01-15'),
  ('mitra@citilink.com', 2, 'Citilink Rewards', '2020-03-20'),
  ('mitra@lionair.com', 3, 'Lion Miles', '2021-06-10'),
  ('mitra@sriwijaya.com', 4, 'Sriwijaya Club', '2021-09-05'),
  ('mitra@batik.com', 5, 'Batik Miles', '2022-02-28');

INSERT INTO HADIAH (kode_hadiah, nama, miles, deskripsi, valid_start_date, program_end, id_penyedia) VALUES
  ('RWD-001', 'Free Ticket Domestik', 15000, 'Tiket gratis rute domestik', '2024-01-01', '2024-12-31', 1),
  ('RWD-002', 'Upgrade Business Class', 20000, 'Upgrade ke business class', '2024-01-01', '2024-12-31', 2),
  ('RWD-003', 'Lounge Access', 5000, 'Akses lounge bandara', '2024-01-01', '2024-12-31', 3),
  ('RWD-004', 'Extra Baggage 20kg', 3000, 'Tambahan bagasi 20kg', '2024-02-01', '2024-12-31', 4),
  ('RWD-005', 'Hotel Voucher', 25000, 'Voucher hotel bintang 4', '2024-03-01', '2024-12-31', 5),
  ('RWD-006', 'Free Ticket Internasional', 40000, 'Tiket gratis rute internasional', '2024-01-01', '2025-06-30', 1),
  ('RWD-007', 'Airport Transfer', 2000, 'Antar jemput bandara', '2024-04-01', '2024-12-31', 2),
  ('RWD-008', 'Diskon 50% Tiket', 8000, 'Diskon 50% untuk 1 tiket', '2024-05-01', '2025-03-31', 3),
  ('RWD-009', 'Priority Check-in', 1500, 'Priority check-in & boarding', '2024-01-01', '2024-12-31', 4),
  ('RWD-010', 'Free Meal Voucher', 1000, 'Voucher makan di bandara', '2024-06-01', '2025-01-31', 5);