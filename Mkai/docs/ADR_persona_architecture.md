# ADR: Persona Behavior as a Core Brain Concern

## Architecture Decision

### Problem
Persona davranışı, kullanıcı deneyimini şekillendiren bir katmandır. Ancak mevcut yapıda bu davranışın hangi katmanda sorumlu olacağı net değildir. Eğer persona davranışı provider katmanına bağlanırsa, farklı model/provider değişikliklerinde kullanıcı deneyimi de değişebilir. Bu, istenmeyen bir ayrışmaya yol açar.

### Seçilen Çözüm
Persona kararını Core Brain’e bırakmak, prompta dönüştürülmesini Prompt Builder’a vermek ve provider katmanının sadece modeli bu prompt ile beslemek üzere kullanılması seçilmiştir.

Bu ayrım, şu nedenlerle tercih edilmiştir:
- Persona kullanıcı deneyimi katmanıdır; model seçimiyle aynı sorumlulukta değildir.
- Provider değişse bile persona davranışı korunur.
- Core Brain, kullanıcı bağlamını analiz edip hangi persona davranışının uygun olduğunu belirler.
- Prompt Builder, bu davranış bilgisini sistem promptuna ve cevap stiline dönüştürür.

### Reddedilen Alternatifler
1. Persona davranışını Provider katmanına eklemek
   - Dezavantajı: model/provider değişimlerinde kullanıcı deneyiminin de değişmesi olurdu.
   - Bu nedenle bu yaklaşım reddedildi.

2. Yeni bir ayrı servis açmak
   - Dezavantajı: mevcut mimariyi gereksiz yere karmaşıklaştırır.
   - Bu nedenle ilk aşamada mevcut katmanları genişletmek daha uygun bulundu.

3. Persona davranışını doğrudan frontend’e bırakmak
   - Dezavantajı: backend mantığı zayıflar ve kullanıcı deneyimi evrensel şekilde yönetilemez.
   - Bu nedenle reddedildi.

### Avantajları
- Persona davranışı, model seçiminden bağımsız olur.
- Kullanıcı deneyimi tutarlı kalır.
- Core Brain ve Prompt Builder sorumlulukları daha nettir.
- Gelecekte farklı persona türleri eklenmesi kolaylaşır.

### Dezavantajları
- İlk etapta biraz daha fazla mimari soyutlama gerektirebilir.
- Core Brain ve Prompt Builder arasında net veri akışı sağlanmazsa davranış tutarsızlaşabilir.

### Geleceğe Etkisi
Bu karar, MKAI’nin uzun vadede daha modüler ve ölçeklenebilir bir yapıya geçmesini sağlar. Persona, çalışma modu, cevap stili ve kullanıcı deneyimi katmanları ileride ayrı ayrı genişletilebilir hale gelir.
