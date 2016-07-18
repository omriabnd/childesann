
python preprocess_heb_childes.py '/cs/++/staff/oabend/nltk_data/corpora/childes/data-xml/' ./../childes_conll/gold_heb.conll

python conversion_to_ud.py ./../childes_conll/gold_heb.conll hebchildes2uni.ini >! ./../childes_conll/gold_heb.converted




