-- Trigger 1: Cek Duplikasi Klaim Missing Miles
CREATE OR REPLACE FUNCTION cek_duplikat_klaim()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM CLAIM_MISSING_MILES
        WHERE flight_number = NEW.flight_number
          AND tanggal_penerbangan = NEW.tanggal_penerbangan
          AND nomor_tiket = NEW.nomor_tiket
          AND email_member = NEW.email_member
    ) THEN
        RAISE EXCEPTION 'Klaim untuk penerbangan "%" pada tanggal "%" dengan nomor tiket "%" sudah pernah diajukan sebelumnya.',
            NEW.flight_number,
            NEW.tanggal_penerbangan,
            NEW.nomor_tiket;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trigger_cek_duplikat_klaim
BEFORE INSERT OR UPDATE ON CLAIM_MISSING_MILES
FOR EACH ROW
EXECUTE FUNCTION cek_duplikat_klaim();

-- Trigger 2: Pembaruan Tier Miles berdasarkan Total Miles
CREATE OR REPLACE FUNCTION update_tier_member()
RETURNS TRIGGER AS $$
DECLARE
    tier_baru VARCHAR(10);
    nama_tier_baru VARCHAR(50);
    nama_tier_lama VARCHAR(50);
BEGIN
    -- Ambil nama tier lama
    SELECT t.nama INTO nama_tier_lama
    FROM TIER t
    WHERE t.id_tier = OLD.id_tier;

    -- Cari tier baru tertinggi yang memenuhi syarat total_miles
    SELECT t.id_tier, t.nama INTO tier_baru, nama_tier_baru
    FROM TIER t
    WHERE NEW.total_miles >= t.minimal_tier_miles
    ORDER BY t.minimal_tier_miles DESC
    LIMIT 1;

    -- Update tier kalau berbeda
    IF tier_baru IS NOT NULL AND tier_baru != OLD.id_tier THEN
        UPDATE MEMBER
        SET id_tier = tier_baru
        WHERE email = NEW.email;

        RAISE NOTICE 'SUKSES: Tier Member "%" telah diperbarui dari "%" menjadi "%" berdasarkan total miles yang dimiliki.',
            NEW.email,
            nama_tier_lama,
            nama_tier_baru;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trigger_update_tier_member
AFTER UPDATE OF total_miles ON MEMBER
FOR EACH ROW
EXECUTE FUNCTION update_tier_member();
