# Test nativo sintetico e riproducibilita

[Stato corrente](../docs/CURRENT_STATUS.md). Il fallimento native-browser a 78c991e e storico: alla baseline b669ec4 il job e success. Non e stata determinata con certezza la causa unica del primo fallimento.

La fixture Linux usa Playwright 1.51.0 e Pillow 12.2.0, versioni provate nell'ambiente dell'assistente; il Chromium 134 associato e soltanto per immagini generate e test isolati, mai per account reali o contenuti web non affidabili. Le dipendenze del prodotto non sono state retrocesse.

Il launcher temporaneo configura la directory delle librerie Python e raccoglie stderr. Il test usa un profilo Chromium temporaneo, un manifest con origine esatta e un host fixture: handshake e JPEG correlati sono stati osservati realmente. Non prova launcher .cmd, registro Windows, consenso Tk o input fisico. Non abilita il test contro profili o desktop reali.
