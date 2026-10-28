# ER diagram (text representation)

```text
BRANCH (1) --------< ACCOUNT (M)
   |                    |
   |                    | (1)
   |                    v
   |                BANK_TRANSACTION (M)
   |
   +--------------< EMPLOYEE (M)
   |
   +--------------< LOAN (M) >-------------- (1) CUSTOMER
                          |
                          | (1)
                          v
                    LOAN_PAYMENT (M)

CUSTOMER (1) -----< ACCOUNT_HOLDER >----- (1) ACCOUNT
                 (junction table)
Customer-to-Account overall cardinality: M:N
```

`ACCOUNT_HOLDER` has composite primary key `(customer_id, account_id)`, with each column also a foreign key.
