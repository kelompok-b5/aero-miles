CREATE OR REPLACE FUNCTION validasi_dan_catat_transfer()
RETURNS TRIGGER AS $$
DECLARE
    saldo_pengirim  INT;

BEGIN
    
    SELECT award_miles
    INTO saldo_pengirim
    FROM MEMBER
    WHERE email = NEW.email_member_1;
    
    IF saldo_pengirim < NEW.jumlah THEN
        RAISE EXCEPTION 
            'ERROR: Saldo award miles tidak mencukupi. Saldo Anda saat ini: % miles, jumlah transfer: % miles.',
            saldo_pengirim,
            NEW.jumlah;
    END IF;

    UPDATE MEMBER
    SET award_miles = award_miles - NEW.jumlah
    WHERE email = NEW.email_member_1;

    UPDATE MEMBER
    SET 
        award_miles = award_miles + NEW.jumlah,
        total_miles = total_miles + NEW.jumlah
    WHERE email = NEW.email_member_2;

    RAISE NOTICE 
        'SUKSES: Transfer % miles dari "%" ke "%" berhasil dicatat.',
        NEW.jumlah,
        NEW.email_member_1,
        NEW.email_member_2;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trigger_transfer_miles
BEFORE INSERT ON TRANSFER
FOR EACH ROW
EXECUTE FUNCTION validasi_dan_catat_transfer();