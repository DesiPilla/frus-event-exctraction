# Political Text Analysis & Event Extraction
The project will focus on automated ‘text-as-data’ methods for the extrac-tion of discrete political (cooperative and conflictive) interactions (i.e., “who did what to whom, and  where/when”) from a large corpora of political texts. Such extracted events are commonly known as political “event data” in the literature. Examples of already-coded event datasets appear in several of the readings below, as well as here: http://eventdata.utdallas.edu/. These extracted political events are typically assigned a geolocation and a date of occurrence down to the calender-day, along with information on each source/target actor for the event (e.g., SYR-Government→SYR-Rebel) and action type (e.g., express intent to cooperate, or impose curfew, or use chemical weapons, etc.).

This special project’s tasks in this case will entail setting up and modifying a variety of existing open source software (found here
https://github.com/openeventdata/phoenix_pipeline) to fully processes and code a large corpus of U.S. diplomatic cables. 
The specific tasks in this regard will entail that we:
 1. Re-structure the raw U.S. diplomatic cables (currently structured as CSV files) into a MongoDB.
 2. Parse the text of each diplomatic cable via Stanford CoreNLP.
 3. Pass the parsed text to a Python-based event coder, such as PETRARCH or PETRARCH2.
 4. Separately pass the parsed text through automated geolocation extraction software such as Mordacai or CLIFF/CLAVIN.
 5. Combine all final data and code into a single GitHub repository.


## Data
The data were scraped from the US State DEpartment FRUS website using R. The title and subtitle are higher-level grouping terms to disambiguate unique documents. The data includes every foreign-policy related document from President Lincoln to President Ford. Each document includes a title, subtitle, document title, body (text), date, and the corresponding president. Additional descriptive columns computed and added for each document include:
* decade
* number of words
  * Total number of entities after splitting on whitespace
* number of capitalized words
  * Determined using a regular expression `'((?<!^)(?<!\. )[A-Z][a-z]+)'`
* percentage of capitalized words 
* language
  * Computed by the passing in the first 100 characters of a document’s body text into the function `langdetect.detect()`.
* unique ID
  * Integer from 1 to 323,294.

The body text was also cleaned by removing irrelevant information. All matches with the regular expression `r'[([]\s?Page\s\d+\s?[)\]]'` were replaced with an empty string, as the page number was often found in the document body but does not add any significant information to the document.

Some documents had missing or incorrect date information (such as September 31st, 1943 or October 8). These documents were removed from the full set of documents, as there were very few of them (58 documents, ~0.018%). The remaining number of documents was 323,294.

We chose to truncate all documents to 1600 words before being processed. This was also chosen due to hardware limitations and to avoid bottlenecks created by one-off documents with extremely long bodies. This number was chosen empirically, after a few hundred had already been parsed. As such, a few number of documents were processed with longer word counts than the stated 1600. This number is not believed to have significant negative effects on the efficacy of parse results. It is standard practice in existing event extractors to use only the first 6 sentences of a text. Of the documents parsed, the first 44.7 sentences of a document were parsed on average, with only 2.6% of documents falling below the 6 sentence threshold. For these reasons, we are comfortable with this criteria for truncating document text.
