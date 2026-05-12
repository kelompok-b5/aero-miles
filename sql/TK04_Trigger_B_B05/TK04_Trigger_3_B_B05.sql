-- TRIGGER 1: Validasi Redeem Hadiah
CREATE OR REPLACE FUNCTION validate_redeem()
RETURNS TRIGGER AS $$
DECLARE
    saldo_miles INT;
    miles_hadiah INT;
    nama_hadiah VARCHAR(100);
    tanggal_mulai DATE;
    tanggal_selesai DATE;
BEGIN
    SELECT award_miles INTO saldo_miles
    FROM MEMBER WHERE email = NEW.email_member;

    SELECT nama, miles, valid_start_date, program_end
    INTO nama_hadiah, miles_hadiah, tanggal_mulai, tanggal_selesai
    FROM HADIAH WHERE kode_hadiah = NEW.kode_hadiah;

    IF CURRENT_DATE NOT BETWEEN tanggal_mulai AND tanggal_selesai THEN
        RAISE EXCEPTION 'ERROR: Hadiah "%" tidak tersedia pada periode ini.', nama_hadiah;
    END IF;

    IF saldo_miles < miles_hadiah THEN
        RAISE EXCEPTION 'ERROR: Saldo award miles tidak mencukupi. Dibutuhkan % miles, saldo Anda: % miles.', miles_hadiah, saldo_miles;
    END IF;

    UPDATE MEMBER 
    SET award_miles = award_miles - miles_hadiah
    WHERE email = NEW.email_member;

    RAISE NOTICE 'SUKSES: Redeem hadiah "%" berhasil. Award miles Anda berkurang % miles.', nama_hadiah, miles_hadiah;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trig_validate_redeem
BEFORE INSERT ON REDEEM
FOR EACH ROW EXECUTE FUNCTION validate_redeem();


-- TRIGGER 2: Sinkronisasi Miles Setelah Pembelian Package
CREATE OR REPLACE FUNCTION sync_miles_after_package()
RETURNS TRIGGER AS $$
DECLARE
    tambahan_miles INT;
BEGIN
    SELECT jumlah_award_miles INTO tambahan_miles
    FROM AWARD_MILES_PACKAGE 
    WHERE id = NEW.id_award_miles_package;

    UPDATE MEMBER
    SET award_miles = award_miles + tambahan_miles,
        total_miles = total_miles + tambahan_miles
    WHERE email = NEW.email_member;

    RAISE NOTICE 'SUKSES: Pembelian package berhasil. Award miles dan total miles Anda bertambah % miles.', tambahan_miles;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trig_sync_miles_after_package
AFTER INSERT ON MEMBER_AWARD_MILES_PACKAGE
FOR EACH ROW EXECUTE FUNCTION sync_miles_after_package();