# Screenshot e preview nel canale nativo

[Stato corrente](../docs/CURRENT_STATUS.md). screen_preview.py compatta in memoria i risultati prima della codifica base64. Le preview grandi sono ridotte entro 1280x800 e JPEG entro 600 KiB, con spazio per il JSON nel limite di 1 MiB. Sorgente massima 16 MiB; il percorso di decodifica/conversione limita anche i pixel. I piccoli payload entro i limiti sono conservati.

Dimensioni originali e preview restano distinte. Le coordinate dichiarate sono pixel dell'immagine sorgente, non una calibrazione verificata del desktop Windows. Il popup accetta solo PNG/JPEG. Nessun file immagine e scritto su disco dalla conversione.

Test di conversione/framing e un vero canale Chromium Linux-Python hanno usato immagini sintetiche; la CI di baseline e verde. La fixture non usa il popup di produzione, non cattura il desktop e non autorizza automaticamente la UI reale. Mancano ritorno automatico dell'immagine alla chat e prove DPI/multi-monitor/Windows. [Dettagli fixture](CI_NATIVE_DIAG.md).
