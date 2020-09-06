# frus-event-exctraction
The project will focus on automated ‘text-as-data’ methods for the extrac- tion of discrete political (cooperative and conflictive) interactions (i.e., “who did what to whom, and  where/when”) from a large corpora of political texts. Such extracted events are commonly known as political “event data” in the literature. Examples of already-coded event datasets appear in several of the readings below, as well as here: http://eventdata.utdallas.edu/. These extracted political events are typically assigned a geolocation
and a date of occurrence down to the calender-day, along with information on each source/target actor for the event (e.g., SYR-Government→SYR-Rebel) and action type
(e.g., express intent to cooperate, or impose curfew, or use chemical weapons, etc.).

This special project’s tasks in this case will entail setting up and modifying a variety of existing open source software (found here
https://github.com/openeventdata/phoenix_pipeline) to fully processes and code a large corpus of U.S. diplomatic cables. 
The specific tasks in this regard will entail that we:
 1. Re-structure the raw U.S. diplomatic cables (currently structured as CSV files) into a MongoDB.
 2. Parse the text of each diplomatic cable via Stanford CoreNLP.
 3. Pass the parsed text to a Python-based event coder, such as PETRARCH or PETRARCH2.
 4. Separately pass the parsed text through automated geolocation extraction software such as Mordacai or CLIFF/CLAVIN.
 5. Combine all final data and code into a single GitHub repository.
