# Piano di resilienza, non test certificati

Aggiornamento: 16 ottobre 2026. [Stato corrente](CURRENT_STATUS.md).

Lease, quarantena, circuit breaker, duplicati QoS 1, partizioni e restore sono scenari da verificare con tracce e commit. Nessuna garanzia di zero doppie esecuzioni o recovery dopo crash deriva da questa nota.

Questo documento non certifica implementazioni o servizi live. Conservare le invarianti mTLS, verifica identita, ACL v1, workspace e approvazioni; non applicare configurazioni storiche come comandi di produzione.

[Versione storica completa alla baseline](https://github.com/ZooL-OhKi/omninode/blob/b669ec404007e01d56b12d502887f695895a8ae1/docs/LIVE_PILOT_MILESTONE_2_RESILIENCY.md). Per procedere usare codice, configurazioni effettive e output delle verifiche, non il nome della fase.
