# Perceptually-Uniform-Plugin
Pistikprogramm olemasolevale graafikatarkvarale, mis aitab kasutajal valida värvitooni eraldiseisva muutujana, mõjutamata seejuures teisi värviomadusi, kasutades selleks kaasaegseid värviteooria lähenemisi ja põhimõtteid. Töö käigus disainitakse ja arendatakse tööriistu, mis arvestavad tajuliselt ühtlaste värviruumide eripärade ja võimalustega.

Repository koosneb hetkel kahest peamisest osast. Tööriistadest, mis on vajalikud varasemate ja autori poolt loodud värvivaliku tööriistade võrdluseks ja algoritmist, mis otsustab millised värvid kasutajaliideses kuvatakse. Lõpufaasides lisandub kolmas osa mis sisaldab algoritmi sisaldavat pistikuprogrammi ennast vastava kasutajaliidesega.

Metodoloogiline lähenemine

#Algoritm ja kasutajaliides:
Eemaldame värvid mida inimsilm teistest värvidesteristada ei suuda kasutajaliideses. Selleks on hetkel plaaanis kasutada monitoride kvaliteedi kontrollis kasutusel olevaid valemeid, kirjutamise hetkel on kasutusel delta94 lihtuse huvides, aga hiljem on plaanis kasutada kaasaegsemat. Kirjutamise hetkel ei ole autor ühtegi kasutajaliidest leidnud, mis sellist väljajätu kriteeriumit kasutaks, levinum on lihtsalt värvi gradienti kasutada, healjuhul lab-i kasutades, et tajupõhisem kate saavutada.
Edasi toimub kasutajaliidese põhine filtreerimine heleduse põhjal. Hetkel on algoritmis kasutusel HSL lihtsuse jaoks, hiljem võetakse kasutusele tajupõhiselt ühtlasem OKLAB-i loonud töögrupi poolt loodud vastav värviruum.
Seejärel prioritiseeritakse kasutajaliideses värvid, mis digimeedias ja graafika disainis kõige tihedamini kasutusel on läbi nende osakaalu suurendamise kasutaja liideses neile suurema pindala eraldades. Seda osa algoritmi veel listud pole.
Hetkel pole veel otsusele jõutud selles osas kas ka liikuda üle HSL-lt inimtajule füsioloogiliselt lähemale vastandvärvide (opponent colour) teooria lähenemisele kasutaja liidese sliderite tasemel ja kui agressiivselt tasub värve ja tausta ringi seada, et kasutajaliideses maksimaalne hulk värve eristatav oleks. Tegemist on olulise küsimusega kuna RGB värvimudel on nn liitev (additive) ja ilma kontekstita pole võimalik seal kõiki värve kuvada nt pruun. 
<img width="1016" height="921" alt="image" src="https://github.com/user-attachments/assets/0c8398be-55f0-4b73-8518-6fd8ad56f019" />

Tööriistad:

Veebiäpp kasutajaliideses olevate värvide analüüsiks ja csv formaati salvestamine hilisema statistika jaoks.

Tausta värvi muutmis võimalus, et väride erisusi paremini näha, algoritmi ja sRGB katte tööriista testimise jaoks.
<img width="1133" height="946" alt="image" src="https://github.com/user-attachments/assets/a95f9544-dc91-47e4-b4c7-6f0e53cef329" />
Pakub ülevaate sellest mitu ainulaadset värvi pikslit on ja mis värvi need on, nende osakaalu kasutajaliideses andmete valideerimiseks enne edasisi statistilisi toimetusi väljastatud csv faili alusel.
<img width="1389" height="972" alt="image" src="https://github.com/user-attachments/assets/a44414b5-b8dc-477d-bc5b-09df01adf061" />

sRGB kattuvuse visualiseermis tööriist

Hetkel renderdab ekraanile kogu sRGB värvigamma ja loeb hiire all oleva värvi. Seda teeb hiire kordinaatide põhjal arvutades algse mappingu kordinaadi ja selle põhjal vastava värvi,mitte ekraanilt otse, kuna CORS ei luba. Lähipäevil lisandub csv failide laadimine ja võimalus sinna laetu salvestada bmp failina tööriista testimise ja andmeteagregeerimis eesmärgil. Rakendus näitab milline osa sRGB-st kaetud on visuaalsel viisil. 

<img width="1881" height="968" alt="image" src="https://github.com/user-attachments/assets/cc03774e-fca9-4c5a-885b-3583f8b3e03a" />

Kuna png, jpg jms pildi formaadid tekitaksid ise kompressiooni käigus täiendavaid värve olukorras kus on tarvilik saada täpne ülevaade sellest kui palju tööriistad sRGB värviruumist katavad ja millise osakaalu millised värvid moodustavad, oli täiendav töö tarvilik. Seetõttu oli vaja töötlemise käigus bmp faile kasutada ja tagada, et kogu tööriista ahel seda formaati toetaks. Mistõttu loodi terminalil põhinev windowsi rakendus bmp formaadis kuvatõmmiste tegemiseks. Algoritmi poolt loodud värvi swatchide puhul, mis salvestati eri valgus astmete juurest peale silmale eristamatute värvide eemaldamist, salvestati tulemus bmp formaadis analüüsiks. Värvi analüüsi veebirakenduses tagati tugi bmp failide üleslaadimiseks ja sRGB kattuvust illustreerivas rakenduses lisati genereeritud või üleslaetud csv failide poolt osaliselt täidetud värvikatte jäädvustamiseks bmp ekspordi tugi andmete ristvalideerimiseks.

Autor Tormi Viirg Tallinna Ülikooli Digitehnoloogiate instituut 
