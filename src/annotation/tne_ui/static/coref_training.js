//--------------Global variables--------------
//var text is dictionary (record) that holds information about the text to be annotated.
var text = { //Record [raw_text: string, title: record [start_index: int, end_index: int, id: int], subtitles: List[record [start_index: int, end_index: int, id: int]], paragraphs: List[record [start_index: int, end_index: int, id: int]].
    'raw_text': "Chilean miner Edison Peña completes the 41st annual New York Marathon Monday, November 8, 2010 Edison Peña, one of the 33 miners who had been trapped underground in the San José copper-gold mine in Copiapó, Chile, participated on Sunday in the 41st annual New York City Marathon. Peña had arrived at the city on Thursday, and had been invited by the New York Road Runners, organizers of the marathon.  Before the marathon began, Peña and Mayor of New York Michael Bloomberg saluted the runners from a stage in Staten Island. The event started at 09:40 local time (14:40 UTC; 11:40 Chile time), and Peña finished at 15:30 (20:30 UTC; 17:30 Chile time), approximately five hours and fifty minutes after the race began. The length of the marathon was about 43 kilometres (26.7 miles). According to Radio Cooperativa, the marathon had a record attendance.'It was worthwhile for me to come this far to run a marathon, because I want to motivate people, ' Peña said. ' In this marathon I struggled. I struggled with myself, I struggled with my own pain, but I didn't throw the towel and made it to the finish line, ' he added. Edison Peña is also planning to run the marathon next year. The Mayor of Copiapó announced an event in his honor.",
    'title': {
        'start_index': 0,
        'end_index': 69
    },
    'subtitles': [{
        'start_index': 70,
        'end_index': 94,
        'id': 0
    }],
    'paragraphs': [{
        'start_index': 95,
        'end_index': 400,
        'id': 0
    }, {
        'start_index': 400,
        'end_index': 851,
        'id': 1
    }, {
        'start_index': 851,
        'end_index': 1234,
        'id': 2
    }]
}
/**
*var nps holds the information about all the NPs that take part in the annotation, and their locations in the original text (field raw_text of var text)
np:record [id: int, start: int, end: int, text: string]
*All the nps that take part on the annotation, including nps added by the user, sould appear on this list
*/
var nps = [{ //List[np]    
    'start_index': 0,
    'text': 'Chilean miner',
    'end_index': 13,
    'id': 0
}, {
    'start_index': 14,
    'text': 'Edison Peña',
    'end_index': 25,
    'id': 1
}, {
    'start_index': 52,
    'text': 'the 41st annual New York Marathon',
    'end_index': 69,
    'id': 2
}, {
    'start_index': 70,
    'text': 'Monday',
    'end_index': 76,
    'id': 3
}, {
    'start_index': 78,
    'text': 'November',
    'end_index': 86,
    'id': 4
}, {
    'start_index': 95,
    'text': 'Edison Peña',
    'end_index': 106,
    'id': 5
}, {
    'start_index': 115,
    'text': 'the 33 miners',
    'end_index': 128,
    'id': 6
}, {
    'start_index': 165,
    'text': 'the San José copper-gold mine',
    'end_index': 194,
    'id': 7
}, {
    'start_index': 198,
    'text': 'Copiapó',
    'end_index': 205,
    'id': 8
}, {
    'start_index': 207,
    'text': 'Chile',
    'end_index': 212,
    'id': 9
}, {
    'start_index': 230,
    'text': 'Sunday',
    'end_index': 236,
    'id': 10
}, {
    'start_index': 240,
    'text': 'the 41st annual New York City Marathon',
    'end_index': 278,
    'id': 11
}, {
    'start_index': 280,
    'text': 'Peña',
    'end_index': 284,
    'id': 12
}, {
    'start_index': 300,
    'text': 'the city',
    'end_index': 308,
    'id': 13
}, {
    'start_index': 312,
    'text': 'Thursday',
    'end_index': 320,
    'id': 14
}, {
    'start_index': 346,
    'text': 'the New York Road Runners',
    'end_index': 371,
    'id': 15
}, {
    'start_index': 373,
    'text': 'organizers of the marathon',
    'end_index': 399,
    'id': 16
}, {
    'start_index': 387,
    'text': 'the marathon',
    'end_index': 399,
    'id': 17
}, {
    'start_index': 409,
    'text': 'the marathon',
    'end_index': 421,
    'id': 18
}, {
    'start_index': 429,
    'text': 'Peña',
    'end_index': 433,
    'id': 19
}, {
    'start_index': 438,
    'text': 'Mayor of New York',
    'end_index': 455,
    'id': 20
}, {
    'start_index': 447,
    'text': 'New York',
    'end_index': 455,
    'id': 21
}, {
    'start_index': 456,
    'text': 'Michael Bloomberg',
    'end_index': 473,
    'id': 22
}, {
    'start_index': 482,
    'text': 'the runners',
    'end_index': 493,
    'id': 23
}, {
    'start_index': 499,
    'text': 'a stage',
    'end_index': 506,
    'id': 24
}, {
    'start_index': 510,
    'text': 'Staten Island',
    'end_index': 523,
    'id': 25
}, {
    'start_index': 525,
    'text': 'The event',
    'end_index': 534,
    'id': 26
}, {
    'start_index': 552,
    'text': 'local time',
    'end_index': 562,
    'id': 27
}, {
    'start_index': 581,
    'text': 'Chile time',
    'end_index': 591,
    'id': 28
}, {
    'start_index': 598,
    'text': 'Peña',
    'end_index': 602,
    'id': 29
}, {
    'start_index': 639,
    'text': 'Chile time',
    'end_index': 649,
    'id': 30
}, {
    'start_index': 666,
    'text': 'five hours',
    'end_index': 676,
    'id': 31
}, {
    'start_index': 681,
    'text': 'fifty minutes',
    'end_index': 694,
    'id': 32
}, {
    'start_index': 701,
    'text': 'the race',
    'end_index': 709,
    'id': 33
}, {
    'start_index': 717,
    'text': 'The length of the marathon',
    'end_index': 743,
    'id': 34
}, {
    'start_index': 731,
    'text': 'the marathon',
    'end_index': 743,
    'id': 35
}, {
    'start_index': 754,
    'text': '43 kilometres',
    'end_index': 767,
    'id': 36
}, {
    'start_index': 769,
    'text': '26.7 miles',
    'end_index': 779,
    'id': 37
}, {
    'start_index': 795,
    'text': 'Radio Cooperativa',
    'end_index': 812,
    'id': 38
}, {
    'start_index': 814,
    'text': 'the marathon',
    'end_index': 826,
    'id': 39
}, {
    'start_index': 831,
    'text': 'a record attendance',
    'end_index': 850,
    'id': 40
}, {
    'start_index': 874,
    'text': 'me',
    'end_index': 876,
    'id': 41
}, {
    'start_index': 901,
    'text': 'a marathon',
    'end_index': 911,
    'id': 42
}, {
    'start_index': 921,
    'text': 'I',
    'end_index': 922,
    'id': 43
}, {
    'start_index': 940,
    'text': 'people',
    'end_index': 946,
    'id': 44
}, {
    'start_index': 950,
    'text': 'Peña',
    'end_index': 954,
    'id': 45
}, {
    'start_index': 966,
    'text': 'this marathon',
    'end_index': 979,
    'id': 46
}, {
    'start_index': 980,
    'text': 'I',
    'end_index': 981,
    'id': 47
}, {
    'start_index': 993,
    'text': 'I',
    'end_index': 994,
    'id': 48
}, {
    'start_index': 1010,
    'text': 'myself',
    'end_index': 1016,
    'id': 49
}, {
    'start_index': 1018,
    'text': 'I',
    'end_index': 1019,
    'id': 50
}, {
    'start_index': 1035,
    'text': 'my own pain',
    'end_index': 1046,
    'id': 51
}, {
    'start_index': 1052,
    'text': 'I',
    'end_index': 1053,
    'id': 52
}, {
    'start_index': 1067,
    'text': 'the towel',
    'end_index': 1076,
    'id': 53
}, {
    'start_index': 1092,
    'text': 'the finish line',
    'end_index': 1107,
    'id': 54
}, {
    'start_index': 1111,
    'text': 'he',
    'end_index': 1113,
    'id': 55
}, {
    'start_index': 1157,
    'text': 'the marathon',
    'end_index': 1169,
    'id': 56
}, {
    'start_index': 1181,
    'text': 'The Mayor of Copiapó',
    'end_index': 1201,
    'id': 57
}, {
    'start_index': 1212,
    'text': 'an event',
    'end_index': 1220,
    'id': 58
}]
/**
*var done_nps is a dictionary that  maps each np id (from nps) to a boolean (true/false)
*An np is marked as "done" when it has been visited and annotated (e.i. assigned to a coref cluster, or entity),
 and the user has not checked (or has unchecked) the "return to this later" option.
*If an np is marked as "done", it means that it does not need to be revisited before the task is considered "complete".
*/
var done_nps = {
    '0': false,
    '1': false,
    '2': false,
    '3': false,
    '4': false,
    '5': false,
    '6': false,
    '7': false,
    '8': false,
    '9': false,
    '10': false,
    '11': false,
    '12': false,
    '13': false,
    '14': false,
    '15': false,
    '16': false,
    '17': false,
    '18': false,
    '19': false,
    '20': false,
    '21': false,
    '22': false,
    '23': false,
    '24': false,
    '25': false,
    '26': false,
    '27': false,
    '28': false,
    '29': false,
    '30': false,
    '31': false,
    '32': false,
    '33': false,
    '34': false,
    '35': false,
    '36': false,
    '37': false,
    '38': false,
    '39': false,
    '40': false,
    '41': false,
    '42': false,
    '43': false,
    '44': false,
    '45': false,
    '46': false,
    '47': false,
    '48': false,
    '49': false,
    '50': false,
    '51': false,
    '52': false,
    '53': false,
    '54': false,
    '55': false,
    '56': false,
	'57': false,
    '58': false
};

//var nps_for_training is a list that hods the ids of the nps that are used for training.

var nps_for_training = [0,1,2,6,13,14,15,16,20,21,22,23,26,31,33,34,37,40,43,51,53,54,55,56,57,58];

var train_nps = nps.filter(np => nps_for_training.includes(np.id));

//var pronouns is a list that hods the ids of the nps that are pronouns.
//At bridging stage these nps should be removed from the items to be annotated and from the coref clusters shown to the users.
var pronouns = [41,43,47,48,49,50,52,55];
/**
*var coref is a list that holds entities (clusters of coreferring nps) created by the user.
*An entity is a record that has an id,a list of members (that are ids of the nps),
and a "source" field that represents the reason why the entity was formed
(the option the user selected which led to creation of a new entity).
*The "source" field can hold values "new","idiomatic","time/date/measurement expression".
*All the options that are compatible with "Same as" (coref) only become sources of new entities,if "Same as" is not selected.
*An np cannot belong to two or more entities.
*An np that is marked as "done" should belong to some entity.*/

var coref = []; //List[entity] //entity: record[id:int,members: List[int],source: string]
/**
var coref_for_reference holds correct entities; serves for checking the user's answers
*/
var coref_for_reference = [{"id":0,"members":[0,1,43,55],"source":"new","selected_preposition":"of"},{"id":1,"members":[2,26,33],"source":"new","selected_preposition":"of"},{"id":2,"members":[6],"source":"new","selected_preposition":"of"},{"id":3,"members":[13,21],"source":"new","selected_preposition":"of"},{"id":4,"members":[14],"source":"time/date/measurement expression","selected_preposition":"of"},{"id":5,"members":[15,16],"source":"new","selected_preposition":"of"},{"id":6,"members":[20,22],"source":"new","selected_preposition":"of"},{"id":7,"members":[23],"source":"new","selected_preposition":"of"},{"id":8,"members":[27],"source":"new","selected_preposition":"of"},{"id":9,"members":[31],"source":"time/date/measurement expression","selected_preposition":"of"},{"id":10,"members":[34],"source":"new","selected_preposition":"of"},{"id":11,"members":[37],"source":"time/date/measurement expression","selected_preposition":"of"},{"id":12,"members":[40],"source":"new","selected_preposition":"of"},{"id":13,"members":[51],"source":"new","selected_preposition":"of"},{"id":14,"members":[53],"source":"idiomatic","selected_preposition":"of"},{"id":15,"members":[54],"source":"new","selected_preposition":"of"},{"id":16,"members":[56],"source":"new"},{"id":17,"members":[57],"source":"new"},{"id":18,"members":[58],"source":"new"}];
// [{"id":0,"members":[0,1,5,12,19,29],"source":"new","selected_preposition":"of"},{"id":1,"members":[2,11,17,18,26,33,35,39],"source":"new","selected_preposition":"of"},{"id":2,"members":[3],"source":"time/date/measurement expression","selected_preposition":"of"},{"id":3,"members":[4],"source":"time/date/measurement expression","selected_preposition":"of"},{"id":4,"members":[6],"source":"new","selected_preposition":"of"},{"id":5,"members":[7],"source":"new","selected_preposition":"of"},{"id":6,"members":[8],"source":"new","selected_preposition":"of"},{"id":7,"members":[9],"source":"new","selected_preposition":"of"},{"id":8,"members":[10],"source":"time/date/measurement expression","selected_preposition":"of"},{"id":9,"members":[13,21],"source":"new","selected_preposition":"of"},{"id":10,"members":[14],"source":"time/date/measurement expression","selected_preposition":"of"},{"id":11,"members":[15,16],"source":"new","selected_preposition":"of"},{"id":12,"members":[20,22],"source":"new","selected_preposition":"of"},{"id":14,"members":[23],"source":"new","selected_preposition":"of"},{"id":15,"members":[24],"source":"new","selected_preposition":"of"},{"id":16,"members":[25],"source":"new","selected_preposition":"of"},{"id":17,"members":[27],"source":"new","selected_preposition":"of"},{"id":18,"members":[28,30],"source":"new","selected_preposition":"of"},{"id":19,"members":[31],"source":"time/date/measurement expression","selected_preposition":"of"},{"id":20,"members":[32],"source":"time/date/measurement expression","selected_preposition":"of"},{"id":21,"members":[34],"source":"new","selected_preposition":"of"},{"id":22,"members":[36],"source":"time/date/measurement expression","selected_preposition":"of"},{"id":23,"members":[37],"source":"time/date/measurement expression","selected_preposition":"of"},{"id":24,"members":[38],"source":"new","selected_preposition":"of"},{"id":25,"members":[40],"source":"new","selected_preposition":"of"}];
/**
*var bridges is a list that holds bridging links created by the user.
*A bridging link can be of two types BridgeLink and  ExternalBridgeLink.
*A BridgeLink represents a bridge whose antecedent is an entity from the text;
it has an id,a "bridge" field that holds the id of the bridge (an np),
a "complement" field that holds the id of the antecedent (an entity),
a "preposition" field that holds the preposition specified by the user,
and a "type" field whose value is always "regular".
*An ExternalBridgeLink represents a bridge whose antecedent is extratextual and was specified by the user;
it has an id,a "bridge" field that holds the id of the bridge (an np),
a "complement" field that holds the string representing the extratextual antecedent,
a "preposition" field that holds the preposition specified by the user,
and a "type" field whose value is always "external".
*Only nps assigned to an entity (coref cluster) can have bridging links with entities or external nps.
*If an np is linked to an entity as a bridge,it cannot belong to the same entity,
and vice versa: if an np belongs to an entity it cannot be linked to the same entity as a bridge.*/

var bridges = []; //List[Union[BridgeLink,ExternalBridgeLink]]//BridgeLink: record[id:int,bridge:int,complement:int,preposition:string,type:string]; ExternalBridgeLink: record[id:int,bridge:int,complement:string,preposition:string,type:string]

var current_np_id = 0; //int //current_np_id is the id of the np that is currently being updated (the one that is highlighted in yellow on the screen)


//--------------Functions that update the nps--------------
//This function creates a new entity and assigns an np to the newly created entity;
//"source" is a string that specifies the reason why the np formed a new entity; it reflects the option selected by the user,for example,"new"
function form_new_entity(np_id,source) {
    try {
        checkIfNotInCluster(np_id); //check if the np does not already belong to an entity (coref cluster)
        var new_entity = {};
        new_entity["id"] = get_next_entity_id();
        new_entity["members"] = [np_id];
        new_entity["source"] = source;
        coref.push(new_entity);
    } catch (e) {
        console.log(e.name + ': ' + e.message);
    }
}

//this function updates the source field of an entity
function update_entity_source(entity_id,source) {
    var my_entity = coref.filter(entity => entity.id == entity_id)[0];
    my_entity["source"] = source;
}

//This function creates bridges (links an np to an entity)
//the argument "entity_id" the id of the entity to which the NP is linked
//the argument prep is a string that reflects the preposition that links the complement to the bridge
function link_to_entity(np_id,entity_id,prep) {
    try {
        checkIfNotSameAs(np_id,entity_id); //check if the np does not belong to the entity
        checkIfBridgingLinkExists(np_id,entity_id); //check if the link does not exist already
        var bridge = {};
        bridge["id"] = get_next_bridge_id();
        bridge["bridge"] = np_id;
        bridge["complement"] = entity_id;
        bridge["preposition"] = prep;
        bridge["type"] = "regular";
        bridges.push(bridge);
    } catch (e) {
        console.log(e.name + ': ' + e.message);
    }
}


//This function creates external bridges (links an np to an external np - one not found in the text)
//the argument "external_np" is a string
//the argument prep is a string that reflects the preposition that links the complement to the bridge
function link_to_external_np(np_id,external_np,prep) {
    var bridge = {};
    bridge["id"] = get_next_bridge_id();
    bridge["bridge"] = np_id;
    bridge["complement"] = external_np;
    bridge["preposition"] = prep;
    bridge["type"] = "external";
    bridges.push(bridge);
}


//This function deletes a bridging link between an np and an entity or an extratextual NP by removing the record of the link from the list of bridges
//"bridge_id" is the id of link to be deleted
//"complement" is the is either an int (the id of the entity from whoch the np is unlinked) or a string (reperesenting the extratextual NP from which the np is unlinked)
function delete_bridge(bridge_id) {
    var bridge_to_delete = _.find(bridges,{
        id: bridge_id
    });
    _.pull(bridges,bridge_to_delete);
}


//This function creates coref links
function add_coref_np_to_entity(np_id,entity_id) {
    try {
        //check if the np has not bridge or member-set links with the entity or does not already belong to another entity
        checkIfNotInCluster(np_id); //check if the np does not already belong to an entity (coref cluster)
        checkIfNotLinkedTo(np_id,entity_id);
        var my_entity = coref.filter(entity => entity.id == entity_id)[0];
        my_entity["members"].push(np_id);
    } catch (e) {
        console.log(e.name + ': ' + e.message);
    }
}

function delete_coref_link(np_id,entity_id) {
    var my_entity = coref.filter(entity => entity.id == entity_id)[0];
    _.pull(my_entity.members,np_id);
    //if the entity has no members anymore,remove the entity from coref
    if (my_entity.members.length == 0) {
        _.pull(coref,my_entity);
    }
}


//This function returns the np that is currently being updated
function get_current_np() {
    var current_np = nps[current_np_id];
    return current_np;
}

//This function returns the np that is currently being updated
function get_current_np_id() {
    var current = current_np_id;
    return current;
}

//This function changes the value of current_np_id
//It is executed when the user finishes updating an np and goes to a new one
function set_current_np(num) {
    current_np_id = num;
    return current_np_id;
}

//This function returns the id of the np that becomes "current" when "Next" is clicked;
//It allows the user to go through the nps in the order in which they appear in the text
//Todo: has to be expanded to take the "return to it later" property into consideration.
function get_next_np_id() {
    var visited_nps = get_visited_nps();
    for (var i = 0; i < nps.length; i++) {
        if ((!visited_nps.includes(i)) && (nps_for_training.includes(i))) {//version for training
            return i;
            break;
        }
    }
    //This part is executed if the first passage through the text is complete (all the nps have been assigned to coref clusters) and the nps that are marked as " not done" have to be revisited
    for (var i = 0; i < nps.length; i++) {
        if (!done_nps[i]) {
            return i;
            break;
        }
    }
    return null; //the task is complete
}


//This function returns the id to be assigned to a newly created entity
function get_next_entity_id() {
    var my_last_entity = _.maxBy(coref,'id')
    if (my_last_entity != undefined) {
        var next_entity_id = my_last_entity.id + 1;
        return next_entity_id;
    }
    return 0;
}

//This function returns the id to be assigned to a newly created bridging link
function get_next_bridge_id() {
    var my_last_bridge = _.maxBy(bridges,'id');
    if (my_last_bridge != undefined) {
        var next_bridge_id = my_last_bridge.id + 1;
        return next_bridge_id;
    }
    return 0;
}


//This function returns a list of ids of visited nps (nps that have already been assigned to a coref cluster,or entity)
function get_visited_nps() {
    var visited_nps = [];
    for (var i = 0; i < coref.length; i++) {
        visited_nps = visited_nps.concat(coref[i]["members"]);
    }
    return visited_nps;
}

//This function serves to present to the user the next np in the text; it is executed when "Next" is clicked
function go_to_next_np() {
    current_np_id = get_next_np_id();
    return current_np_id;
}


//This function marks an np as "done" or "not done"
//An np should be marked as done whenever the annotation of an np is finished and the "return to this later" option is not checked.
//An np shpuld be marked as "not done" again,whenever a scratch out idtem on the item pane is clicked.
function mark_done(np_id,isDone = true) {
    done_nps[np_id] = isDone;
}


//--------------Functions that return lists/dictionaries to reflect the current state of the annotation--------------

//This function returns the current state of an np
function show_np_status(np_id) {
    var my_np = nps.filter(np => np.id == np_id)[0];
    var np_to_show = my_np;
    if (get_visited_nps().includes(np_id)) {
        //coref
        var entity = coref.filter(entity => entity.members.includes(np_id))[0];
        var entity_id = entity["id"];
        np_to_show["belongs_to_entity"] = entity_id;

        //label from the coref stage
        //if this np formed a new entity,the label is the source of the entity; otherwise - "same as..."
        var label = (entity.members[0] == np_id ? entity.source : 'same as...');
        np_to_show["label"] = label;

        //bridges
        var my_bridges = bridges.filter(lnk => lnk.bridge == np_id);
        if (my_bridges.length > 0) {
            np_to_show["linked_to_entities"] = []; //bridges
            for (var i = 0; i < my_bridges.length; i++) {
                np_to_show["linked_to_entities"].push(my_bridges[i]["complement"]);
            }
        }
    }
    return (np_to_show);
}


//This function returns a list of nps with "idiomatic" and "time/date/measurement" removed
function get_nps_for_bridging_stage() {
    var filtered_nps = nps.filter(np => (!(["idiomatic","time/date/measurement expression"].includes(show_np_status(np.id)["label"]) || pronouns.includes(np.id))));
    return filtered_nps;
}


//This function returns a list of all the nps with currently existing annotations
function annotation_status() {
    annotations = [];
    for (var i = 0; i < nps.length; i++) {
        annotations.push(show_np_status(nps[i]["id"]));
    }
    return (annotations);
}


//--------------Invariants an checks--------------

//This function checks if np a belongs to coref cluster (entity) b;
//It is used when forming bridging links to check if an np is not being linked to its own cluster;
//Throws an error if a belongs to b
function checkIfNotSameAs(a,b) {
    var my_entity = coref.filter(entity => entity.members.includes(a))[0];
    var my_entity_id = -1;
    if (my_entity != undefined) {
        var my_entity_id = my_entity["id"];
    }
    if (my_entity_id == b) {
        throw new Error('An np that belongs to an entity,cannot form a bridging or member-set link with the same entity');
    }
}

//This function checks if np a is linked to coref cluster (entity) b as a bridge;
//It is used when assigning an np to a coref cluster (entity);
//Throws an error if a is linked to b;
function checkIfNotLinkedTo(a,b) {
    var my_links = bridges.filter(lnk => lnk.bridge == a);
    var my_link = my_links.filter(lnk => lnk.complement == b);
    if (my_link.length > 0) { //a is linked to b as a bridge
        throw new Error('An np that is linked to an entity as a bridge,cannot be assigned to the same entity');
    }
}


//This function checks if np already belongs to a coref cluster (entity);
//It is used when assigning an np to a coref cluster (entity),a new one or an existing one.
//Throws an error if the np already belongs to another coref cluster;
function checkIfNotInCluster(np_id) {
    var my_entity = coref.filter(entity => entity.members.includes(np_id))[0];
    if (my_entity != undefined) {
        throw new Error('An np that belongs to an entity,cannot be assigned to an entity again');
    }
}

//This function checks if a bridging link already exists;
//It is used when creating new bridging links;
//Throws an error if a link with "bridge" a,and "complement" b already exists;
function checkIfBridgingLinkExists(a,b) {
    var my_link = bridges.filter(lnk => (lnk.bridge == a && lnk.complement == b));
    if (my_link.length > 0) { //a link between a and b alredy exists
        throw new Error('A bridging link between this np and this complement already exists,');
    }
}

//for training
nps.forEach((np) => {
if (!nps_for_training.includes(np.id)){
mark_done(np.id);
}
});



