----------------silver fact transaction table----------------------------------
CREATE OR REPLACE TABLE `remittance-realtime-de.silver.fact_transactions` AS
SELECT
    Tranno AS transaction_id,
    refno,
    agentid,

    UPPER(TRIM(agentname)) AS agent_name,
    UPPER(TRIM(Branch)) AS branch_name,

    CustomerId,
    SenderName,
    UPPER(TRIM(SenderCountry)) AS sender_country,
    ReceiverName,
    UPPER(TRIM(ReceiverCountry)) AS receiver_country,

    paidAmt AS paid_amount,
    receiveAmt AS receive_amount,
    ExchangeRate AS exchange_rate,

    UPPER(TRIM(TransStatus)) AS transaction_status,
    UPPER(TRIM(status)) AS status,

    UPPER(TRIM(paymentType)) AS payment_type,
    UPPER(TRIM(TransferType)) AS transfer_type,
    DOT

FROM `remittance-realtime-de.new_bronze.raw_remittance_transactions`

-----------------------------silver.dim_agent----------------------------
CREATE OR REPLACE TABLE `remittance-realtime-de.silver.dim_agent` AS
SELECT DISTINCT
    agentid,
    UPPER(TRIM(agentname)) AS agent_name,
    Branch_code,
    UPPER(TRIM(Branch)) AS branch_name
FROM `remittance-realtime-de.new_bronze.raw_remittance_transactions`

----------------------------silver.dim_customer---------------------------
CREATE OR REPLACE TABLE `remittance-realtime-de.silver.dim_customer` AS
SELECT DISTINCT
    CustomerId,

    UPPER(TRIM(SenderName)) AS sender_name,

    SenderAddress,
    SenderCity,
    SenderCountry,

    SenderPhoneno,
    sender_mobile,

    SenderEmail,

    SenderCompany,
    senderPassport,
    SenderNativeCountry

FROM `remittance-realtime-de.new_bronze.raw_remittance_transactions`
WHERE SenderName IS NOT NULL;
----------------------------silver.dim_receiver----------------------------
CREATE OR REPLACE TABLE `remittance-realtime-de.silver.dim_receiver` AS
SELECT DISTINCT

    ReceiverID,

    UPPER(TRIM(ReceiverName)) AS receiver_name,

    ReceiverAddress,
    ReceiverPhone,
    receiver_mobile,

    ReceiverCity,
    ReceiverCountry,

    ReceiverRelation,

    ReceiverIDDescription,

    receiverEmail

FROM `remittance-realtime-de.new_bronze.raw_remittance_transactions`
WHERE ReceiverName IS NOT NULL;