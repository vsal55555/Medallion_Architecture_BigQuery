--------------------------------------------------------------------------------------
--Then we'll build Gold tables:
----------------gold.agent_performance--------------------------------------------
CREATE OR REPLACE TABLE `remittance-realtime-de.gold.agent_performance` AS
SELECT
    agentid,
    agent_name,
    branch_name,

    COUNT(*) AS transaction_count,

    SUM(paid_amount) AS total_paid_amount,

    SUM(receive_amount) AS total_received_amount,

    AVG(paid_amount) AS avg_transaction_size

FROM `remittance-realtime-de.silver.fact_transactions`

GROUP BY
    agentid,
    agent_name,
    branch_name
ORDER BY 
    agent_name ASC,
    branch_name ASC,
    TOTAL_PAID_AMOUNT DESC;
	
CREATE OR REPLACE TABLE `remittance-realtime-de.gold.agent_performance_new` AS
SELECT
    agentid,

    CASE
        WHEN agent_name = 'KIST REMIT AGENT'
            THEN 'LOCAL AGENT'

        WHEN agent_name = 'KIST BANK'
            THEN 'LOCAL BANK'

        WHEN agent_name = 'SUMERU INTL REMIT'
            THEN 'ABC INTL REMIT'

        WHEN agent_name = 'BAHRAIN INDIA INTERNATIONAL EXCHANGE CO BSC'
            THEN 'INDONEPAL INTL REMIT'

        WHEN agent_name = 'BEXMONEY BAHRAIN EXPRESS EXCHANGE WLL'
            THEN 'BAHRAIN INTL REMIT'

        ELSE 'OTHER AGENT'
    END AS masked_agent_name,

    branch_name,

    COUNT(*) AS transaction_count,
    SUM(paid_amount) AS total_paid_amount,
    SUM(receive_amount) AS total_received_amount,
    AVG(paid_amount) AS avg_transaction_size

FROM `remittance-realtime-de.silver.fact_transactions`

GROUP BY
    agentid,
    masked_agent_name,
    branch_name

ORDER BY
    masked_agent_name ASC,
    branch_name ASC,
    total_paid_amount DESC;
---------------------------------------------gold.country_corridor-----------------------------------
CREATE OR REPLACE TABLE `remittance-realtime-de.gold.country_corridor` AS
SELECT

    Sender_Country,
    Receiver_Country,

    COUNT(*) AS transaction_count,

    SUM(paid_amount) AS total_paid_amount,

    SUM(receive_amount) AS total_received_amount

FROM `remittance-realtime-de.silver.fact_transactions`

GROUP BY
    Sender_Country,
    Receiver_Country;
---------------------------------------------gold.monthly_summary---------------------------------------
CREATE OR REPLACE TABLE `remittance-realtime-de.gold.monthly_summary` AS
SELECT

    EXTRACT(YEAR FROM DOT) AS year,
    EXTRACT(MONTH FROM DOT) AS month,

    COUNT(*) AS transaction_count,

    SUM(paid_amount) AS total_paid_amount,

    SUM(receive_amount) AS total_received_amount

FROM `remittance-realtime-de.silver.fact_transactions`

GROUP BY
    year,
    month
ORDER BY
YEAR DESC,
TRANSACTION_COUNT DESC;

---------------------------------------------gold.commission_summary-------------------------------------
CREATE OR REPLACE TABLE `remittance-realtime-de.gold.commission_summary` AS
SELECT

    agentid,
    agentname,

    COUNT(*) AS transaction_count,

    SUM(SAFE_CAST(imeCommission AS NUMERIC)) AS ime_commission,

    SUM(SAFE_CAST(bankCommission AS NUMERIC)) AS bank_commission,

    SUM(SAFE_CAST(senderCommission AS NUMERIC)) AS sender_commission,

    SUM(SAFE_CAST(receiverCommission AS NUMERIC)) AS receiver_commission

FROM `remittance-realtime-de.new_bronze.raw_remittance_transactions`

GROUP BY
    agentid,
    agentname
ORDER BY
    transaction_count desc,
    ime_Commission desc,
    bank_Commission desc,
    sender_Commission desc,
    receiver_Commission desc;