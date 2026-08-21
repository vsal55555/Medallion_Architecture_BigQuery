'''
Then we'll mask PII:
--Sensitive Columns
---Customer----
SenderPhoneno
sender_mobile
SenderEmail
senderPassport
Create Masked Customer Dimension '''

CREATE OR REPLACE TABLE `remittance-realtime-de.silver.dim_customer` AS
SELECT DISTINCT

    CustomerId,

    UPPER(TRIM(SenderName)) AS sender_name,

    SenderAddress,
    SenderCity,
    SenderCountry,

    -- Phone Masking
    CASE
        WHEN SenderPhoneno IS NOT NULL
        THEN CONCAT('XXXXXXX', RIGHT(SenderPhoneno, 3))
    END AS sender_phone_masked,

    CASE
        WHEN sender_mobile IS NOT NULL
        THEN CONCAT('XXXXXXX', RIGHT(sender_mobile, 3))
    END AS sender_mobile_masked,

    -- Email Masking
    CASE
        WHEN SenderEmail IS NOT NULL
        THEN CONCAT(
            SUBSTR(SenderEmail,1,1),
            '***',
            REGEXP_EXTRACT(SenderEmail,r'@.*')
        )
    END AS sender_email_masked,

    -- Passport Masking
    CASE
        WHEN senderPassport IS NOT NULL
        THEN CONCAT(
            '*****',
            RIGHT(senderPassport,4)
        )
    END AS sender_passport_masked,

    SenderCompany,
    SenderNativeCountry

FROM `remittance-realtime-de.new_bronze.raw_remittance_transactions`;
----Receiver----
ReceiverPhone
receiver_mobile
receiverEmail
ReceiverID
Step 2: Create Masked Receiver Dimension
CREATE OR REPLACE TABLE `remittance-realtime-de.silver.dim_receiver` AS
SELECT DISTINCT

    -- Receiver ID Masked
    CASE
        WHEN ReceiverID IS NOT NULL
        THEN CONCAT(
            '*****',
            RIGHT(ReceiverID,4)
        )
    END AS receiver_id_masked,

    UPPER(TRIM(ReceiverName)) AS receiver_name,

    ReceiverAddress,

    CASE
        WHEN ReceiverPhone IS NOT NULL
        THEN CONCAT('XXXXXXX', RIGHT(ReceiverPhone,3))
    END AS receiver_phone_masked,

    CASE
        WHEN receiver_mobile IS NOT NULL
        THEN CONCAT('XXXXXXX', RIGHT(receiver_mobile,3))
    END AS receiver_mobile_masked,

    ReceiverCity,
    ReceiverCountry,

    ReceiverRelation,
    ReceiverIDDescription,

    CASE
        WHEN receiverEmail IS NOT NULL
        THEN CONCAT(
            SUBSTR(receiverEmail,1,1),
            '***',
            REGEXP_EXTRACT(receiverEmail,r'@.*')
        )
    END AS receiver_email_masked

FROM `remittance-realtime-de.new_bronze.raw_remittance_transactions`;