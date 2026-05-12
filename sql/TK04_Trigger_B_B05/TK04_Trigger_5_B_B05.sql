-- 5.1 Trigger untuk sinkronisasi miles pada klaim penerbangan
CREATE OR REPLACE FUNCTION sinkronisasi_miles_klaim()
RETURNS TRIGGER AS $$
DECLARE
    v_miles_tambah INT := 1000;
BEGIN
    IF NEW.status_penerimaan = 'Disetujui' AND OLD.status_penerimaan = 'Menunggu' THEN
        UPDATE MEMBER
        SET award_miles = award_miles + v_miles_tambah,
            total_miles = total_miles + v_miles_tambah
        WHERE email = NEW.email_member;
 
        RAISE NOTICE 'SUKSES: Total miles Member "%" telah diperbarui. Miles ditambahkan: % miles dari klaim penerbangan "%".',
            NEW.email_member,
            v_miles_tambah,
            NEW.flight_number;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
 

CREATE OR REPLACE TRIGGER trigger_sinkronisasi_miles_klaim
AFTER UPDATE OF status_penerimaan ON CLAIM_MISSING_MILES
FOR EACH ROW
EXECUTE FUNCTION sinkronisasi_miles_klaim();

-- 5.2 Procedure untuk menampilkan top 5 member berdasarkan total miles
CREATE OR REPLACE PROCEDURE sp_top5_member_total_miles()
LANGUAGE plpgsql
AS $$
DECLARE
    v_email_pertama VARCHAR;
    v_miles_pertama INT;
BEGIN
    SELECT m.email, m.total_miles
    INTO v_email_pertama, v_miles_pertama
    FROM MEMBER m
    ORDER BY m.total_miles DESC
    LIMIT 1;
 
    RAISE NOTICE 'SUKSES: Daftar Top 5 Member berdasarkan total miles berhasil diperbarui, dengan peringkat pertama "%" memiliki % miles.',
        v_email_pertama,
        v_miles_pertama;
END;
$$;
