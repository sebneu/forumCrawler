# Annotated Hate Speech Datasets

## Information:

3 Types of Hate Speech:

* Hate towards Muslim refugees
* Hate against political opinions
* Sexist comments regarding woman

Each dataset consists of 300 annotated user comments.
For annotation we added the two variables HateSpeech and Severity
HateSpeech is set to 0 by default and will be set to 1 if a posting contains
hate speech. Severity should work as a measurement on how severe a posting
is, with a range from 0 to 3. The default value is again 0 if the posting
is not offensive, when the posting contains hate speech the value increases
with severity. This variable is very subjective and should only be used as
guidance for future works. <br/>
We also added the variable newspaper which has the value 1, 2 or 3 for the newspaper the comments origins from.


## Import to Mongo DB

The following commands import all 4 annotated datasets into your MongoDB into the new DB HateSpeechTypes. <br/>
You can change this to any name you like or take the name of an existing DB. <br/>
The filepaths needs to be adjusted to where you store the data dumps. <br/>

`mongorestore  --db HateSpeechTypes --collection sampleTypeMuslimRefugee  c:\annotated_HS_Datasets\hs_type1\sampleTypeMuslimRefugee.bson`

`mongorestore  --db HateSpeechTypes --collection sampleTypeOpinionLeft    c:\annotated_HS_Datasets\hs_type2_l\sampleTypeOpinionLeft.bson`

`mongorestore  --db HateSpeechTypes --collection sampleTypeOpinionRight   c:\annotated_HS_Datasets\hs_type2_r\sampleTypeOpinionRight.bson`

`mongorestore  --db HateSpeechTypes --collection sampleTypeSexist         c:\annotated_HS_Datasets\hs_type3\sampleTypeSexist.bson`
