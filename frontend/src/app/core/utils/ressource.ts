// Lire la valeur d'une ressource HTTP sans exception si la requête a échoué
// (httpResource lève une erreur à la lecture de value() en état d'erreur).
export function valeurs<T>(ressource: { hasValue(): boolean; value(): T[] }): T[] {
  return ressource.hasValue() ? ressource.value() : [];
}
