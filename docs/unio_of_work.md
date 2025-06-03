┌─────────────┐   publish()                     ┌─────────────┐
│  Domain層   │  (メモリに蓄積)                  │   UseCase   │
│ Project etc │ ───────────────┐              ┌─► executes   │
└─────────────┘                │              │ └─────────────┘
                               │ events       │     ▲
                               ▼              │     │
                         ┌─────────────┐      │  with UnitOfWork
                         │DomainEvents │      │     │
                         └─────────────┘      ▼     │
                                   flush_to_outbox() │
                         ┌───────────────────────────┴────┐
                         │      UnitOfWork (new)          │
                         │  ├─ SQLAlchemy Session         │
                         │  └─ DomainEventPublisher       │
                         │        (events property)       │
                         └──────────────┬─────────────────┘
                                        │ commits same Tx
                                        ▼
                              ┌────────────────┐
                              │ Outboxテーブル │  ◄─ INSERT (Tx内)
                              └────────────────┘