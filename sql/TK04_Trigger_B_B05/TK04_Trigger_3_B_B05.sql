CREATE OR REPLACE FUNCTION cek_duplikat_klaim()
RETURNS TRIGGER AS $$
DECLARE
    existing_count INT;
BEGIN
    SELECT COUNT(*) INTO existing_count
    FROM CLAIM_MISSING_MILES
    WHERE flight_number = NEW.flight_number
      AND tanggal_penerbangan = NEW.tanggal_penerbangan
      AND nomor_tiket = NEW.nomor_tiket
      AND email_member = NEW.email_member;

    IF existing_count > 0 THEN
        RAISE EXCEPTION 'Klaim untuk penerbangan "%" pada tanggal "%" dengan nomor tiket "%" sudah pernah diajukan sebelumnya.',
            NEW.flight_number,
            NEW.tanggal_penerbangan,
            NEW.nomor_tiket;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trigger_cek_duplikat_klaim
BEFORE INSERT ON CLAIM_MISSING_MILES
FOR EACH ROW
EXECUTE FUNCTION cek_duplikat_klaim();