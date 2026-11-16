"""İsteğe bağlı isim tanıma (PERSON): Hugging Face'teki Türkçe NER modeliyle.

`presidio-tr[ner]` ekini (transformers + torch) ister. Model ilk kullanımda indirilir (~440 MB).
"""

from presidio_analyzer import RecognizerResult
from presidio_analyzer.predefined_recognizers import HuggingFaceNerRecognizer

MODEL_NAME = "akdeniz27/bert-base-turkish-cased-ner"


class TurkishPersonRecognizer(HuggingFaceNerRecognizer):
    """Modelin yalnızca kişi (PER) tahminlerini PERSON olarak döndürür.

    Model yer (LOC) ve kurum (ORG) da etiketler; Presidio eşlenmemiş etiketleri olduğu gibi geçirdiği için
    bunlar burada atılır. `aggregation_strategy="first"`, küçük ya da büyük harfle yazılmış isimlerin alt kelime
    parçalarına bölünmesini önler ("ayşe yılmaz" → "ay" + "şe yılmaz" olmaz).
    """

    def __init__(self, model_name: str = MODEL_NAME, device: str = "cpu") -> None:
        super().__init__(
            supported_entities=["PERSON"],
            name=type(self).__name__,
            supported_language="tr",
            model_name=model_name,
            label_mapping={"PER": "PERSON"},
            aggregation_strategy="first",
            device=device,
        )

    def analyze(self, text, entities, nlp_artifacts=None) -> list[RecognizerResult]:
        return [r for r in super().analyze(text, entities, nlp_artifacts) if r.entity_type == "PERSON"]
