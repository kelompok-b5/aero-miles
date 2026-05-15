-- Pemeriksaan Duplikasi Email saat Registrasi
CREATE OR REPLACE FUNCTION periksa_duplikasi_email()
RETURNS TRIGGER AS $$
BEGIN

    IF EXISTS (
        SELECT 1
        FROM PENGGUNA
        WHERE LOWER(email) = LOWER(NEW.email)
    ) THEN
        RAISE EXCEPTION
            'ERROR: Email "%" sudah terdaftar, silakan gunakan email lain.',
            NEW.email;
    END IF;

    NEW.email := LOWER(NEW.email);

    RETURN NEW;

END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trigger_duplikasi_email
BEFORE INSERT ON PENGGUNA
FOR EACH ROW
EXECUTE FUNCTION periksa_duplikasi_email();


-- Verifikasi Kredensial saat Login
CREATE OR REPLACE PROCEDURE verifikasi_login(
    input_email VARCHAR,
    input_password VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    stored_hash VARCHAR;
BEGIN

    SELECT password
    INTO stored_hash
    FROM PENGGUNA
    WHERE LOWER(email) = LOWER(input_email);

    IF NOT FOUND THEN
        RAISE EXCEPTION
            'Email atau password salah, silakan coba lagi.';
    END IF;

    IF stored_hash <> crypt(input_password, stored_hash) THEN
        RAISE EXCEPTION
            'Email atau password salah, silakan coba lagi.';
    END IF;

END;
$$;