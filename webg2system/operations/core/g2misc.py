#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
...
"""

# standard library imports
import datetime as dt
import logging
import sqlite3
from xml.dom import minidom

#specific imports
from g2suiteparser import G2SuiteParser
import utilities

# TODO 

class G2Source(object):
    """
    """

    def __init__(self, area, item):
        """
        Inputs:
            area
            item - A G2Item instance
        """

        self.logger = logging.getLogger("G2ProcessingLine.G2Source")
        self.logger.debug("__init__ method called")
        self.item = item
        self.specificNames = []
        self.source = None
        self.generalSource = None
        self.area = None
        self.sourcesXMLFile = utilities.get_new_settings()["settingsFiles"]["sourceSettings"]
        sourcesXMLDoc = minidom.parse(self.sourcesXMLFile)
        for areaEl in sourcesXMLDoc.getElementsByTagName("area"):
            if area == areaEl.firstChild.nodeValue:
                self.area = area
                sourceEl = areaEl.parentNode.parentNode
                specificNamesEl = sourceEl.getElementsByTagName("specificNames")[0]
                self.generalSource = sourceEl.getAttribute("name")
                for specNameEl in specificNamesEl.getElementsByTagName("specificName"):
                    self.specificNames.append({
                        "name" : specNameEl.getAttribute("name"),
                        "activeFrom" : dt.datetime.strptime(specNameEl.getAttribute("activeFrom"), "%Y%m%d%H%M"),
                        "activeUntil" : dt.datetime.strptime(specNameEl.getAttribute("activeUntil"), "%Y%m%d%H%M")})
        self.source = self.get_name(self.item.timeslotDT)
        self.logger.debug("__init__ method exiting")

    def get_name(self, timeslotDT):
        """
        ...
        """

        self.logger.debug("get_name method called.")
        name = None
        for nameDict in self.specificNames:
            if nameDict["activeFrom"] <= timeslotDT < nameDict["activeUntil"]:
                name = nameDict["name"]
        self.logger.debug("name: %s" % name)
        self.logger.debug("get_name method exiting.")
        return name

    def __repr__(self):
        return "%s(area=%r, source=%r)" % (self.__class__.__name__, self.area,
                                           self.source)


class G2DatabaseManager(object):
    """
    ...
    """

    #databaseFile = "/home3/geoland/GEOLAND2/OPERATIONAL/DATABASES/g2_db.sqlite"

    def __init__(self, opStatus):
        """
        ...
        """

        self.logger = logging.getLogger("G2ProcessingLine.G2DatabaseManager")
        self.logger.debug("__init__ method called")
        self.databaseFile = utilities.get_settings(opStatus)["database"]
        self.connection = sqlite3.connect(self.databaseFile)
        self._turn_on_foreign_keys()
        self.logger.debug("__init__ method exiting")

    def find_process(self, packageObj):
        """
        Return a process's ID, in case it is already present in the database.

        Inputs: packageObj - An instance of the G2Package class or any of its
                             derived classes
        Returns: an integer specifying the process ID of a previous process
                 that has been found in the database, or 'None' in case this
                 process is new.
        """

        self.logger.debug("find_process method called")
        query = """
                SELECT DISTINCT p.proc_id
                FROM pa_fi_pr pfp, process p
                WHERE p.proc_id = pfp.proc_id 
                AND pfp.pack_name = ?
                AND p.timeslot = ?
                AND pfp.pack_area = ?
                AND pfp.pack_source = ?;
                """
        queryParams = (
                packageObj.name, 
                packageObj.timeslotDT.strftime("%Y-%m-%d %H:%M:%S"),
                packageObj.sourceObj.area,
                packageObj.sourceObj.source)
        procID = None
        for row in self.connection.execute(query, queryParams):
            procID = int(row[0])
        self.logger.debug("find_process method exiting")
        return procID

    def insert_process(self, packageObj, status, processingMode, inputFilesDict):
        """
        Insert a new process in the database, which means inserting new records
        in the 'process' and 'pa_fi_pr' tables.
        """

        procID = self._insert_process_record(packageObj, status, processingMode)
        self._insert_pfp_record(packageObj, procID, inputFilesDict)

    def update_process(self, package, procID, status, processingMode, inputFilesDict):
        """
        Update an exiting process's information in the database. 

        Inputs:

        
        Updating a process means altering the relevant records in the 
        'process' and 'pa_fi_pr' tables.
        """

        self._update_process_record(procID, status, processingMode)
        self._update_pfp_record(package, procID, inputFilesDict)

    def _insert_process_record(self, packageObj, status, processingMode):
        """
        Insert a new record in the 'process' table of the database.

        Inputs: packageObj - An instance of the G2Package class or any of its
                             derived classes
                status - an integer specifying the status of the process. 
                processingMode - a string indicating if the process has been run
                                  in 'NRT' or 'reprocess' modes.

        Returns: an integer specifying the id of the process.
        """

        self.logger.debug("insert_process_record method called")
        insertQuery = """
                INSERT INTO process
                (timeslot, status, processing_mode)
                VALUES
                (?, ?, ?)
                """
        insertQueryParams = (packageObj.timeslotDT.strftime("%Y-%m-%d %H:%M:%S"), status, processingMode)
        self.logger.debug("insertQueryParams:" + insertQueryParams)
        self.connection.execute(insertQuery, insertQueryParams)
        getIDQuery = "SELECT last_insert_rowid()"
        procID = int([row[0] for row in self.connection.execute(getIDQuery)][0])
        self.connection.commit()
        self.logger.debug("insert_process method exiting")
        return procID

    def _insert_pfp_record(self, packageObj, procID, inputFilesDict):
        """

        Insert new records in the 'pa_fi_pr' table of the database.

        Inputs: packageObj - An instance of the G2Package class or any of its
                             derived classes
                procID - an integer specifying the process id of the
                         process being run.
                inputFilesDict - a dictionary with G2File objects as
                             keys and pathLists as values
        """

        self.logger.debug("insert_pfp method called")
        query = """
                INSERT INTO pa_fi_pr
                (file_name, file_area, file_source, file_role,
                file_timeslot, num_actual_files,
                pack_name, pack_mode, pack_area, pack_source,
                mode_version, proc_id)
                VALUES
                (?,?,?,?,?,?,?,?,?,?,?,?)
                """
        packageQueryParams = (
                packageObj.name, packageObj.mode, packageObj.sourceObj.area,
                packageObj.sourceObj.source, packageObj.version)
        allOutputs, outputFilesDict = packageObj.find_outputs()
        filesDict = {
                'input' : inputFilesDict,
                'output' : outputFilesDict}
        for fileRole, filesPathsDict in filesDict.iteritems():
            for fileObj, pathList in filesPathsDict.iteritems():
                numFiles = len(pathList)
                # testing ...
                if numFiles > 0:
                    fileQueryParams = (
                            fileObj.name, fileObj.sourceObj.area,
                            fileObj.sourceObj.source, fileRole,
                            fileObj.timeslotDT.strftime("%Y-%m-%d %H:%M:%S"),
                            numFiles)
                    queryParams = fileQueryParams + packageQueryParams + (procID,)
                    self.connection.execute(query, queryParams)
                # end of testing ...
        self.connection.commit()
        self.logger.debug("insert_pfp method exiting")

    def _remove_process_record(self, procID):
        """
        Remove a record in the 'process' table of the database.

        Inputs: procID - an integer specifying the process id of the record to update
        """

        self.logger.debug("update_process method called")
        removeQuery = "DELETE FROM process WHERE proc_id = ?"
        self.connection.execute(removeQuery, (procID,))
        self.connection.commit()
        self.logger.debug("update_process method exiting")

    def _turn_on_foreign_keys(self):
        """
        Execute the SQLite pragma command that turns on foreign key enforcement.
        """

        self.logger.debug("_turn_on_foreign_keys method called")
        self.connection.execute('PRAGMA foreign_keys=ON')
        for row in self.connection.execute('PRAGMA foreign_keys'):
            result = row[0]
        self.logger.debug("_turn_on_foreign_keys method exiting")
        return result

    def _update_pfp_record(self, package, procID, inputFilesDict):
        """
        Update records in the 'pa_fi_pr' table of the database.
        """

        self.logger.debug("update_pfp method called")
        # first delete the existing records and then insert new ones
        removeQuery = "DELETE FROM pa_fi_pr WHERE proc_id = ?"
        removeQueryParams = (procID,)
        self.connection.execute(removeQuery, removeQueryParams)
        self._insert_pfp_record(package, procID, inputFilesDict)
        self.logger.debug("update_pfp method exiting")

    def _update_process_record(self, procID, status, processingMode):
        """
        Update a record in the 'process' table of the database.

        Inputs: procID - an integer specifying the process id of the record to update
                status - an integer specifying the status of the process. 
                processingMode - a string indicating if the process has been run
                                 in 'NRT' or 'reprocess' modes.
        """

        self.logger.debug("update_process method called")
        query = """
                UPDATE process
                SET status = ?, processing_mode = ?
                WHERE proc_id = ?
                """
        queryParams = (status, processingMode, procID)
        self.connection.execute(query, queryParams)
        self.connection.commit()
        self.logger.debug("update_process method exiting")

    def check_package_consistency(self, suiteName="geoland2NRT"):
        """
        Test if all the packages defined in the XML settings are present in the database.

        Returns a tuple with the following values:
            
            - a boolean indicating if the DB is consistent with the XML settings
            - a list of strings indicating the packages_modes missing from the DB
        """
        selectQuery = "SELECT name, operation_mode FROM package"
        definedPackages = [row for row in self.connection.execute(selectQuery)]

        sp = G2SuiteParser(suiteName)
        suiteNodes = list(sp.get_nodes_data(sp.suiteNode))
        missingPackages = []
        dbIsConsistent = False
        for nodeName, nodeMode, nodeArea, nodeDBPackage in suiteNodes:
            if ((nodeDBPackage, nodeMode) not in definedPackages) and (nodeMode is not None):
                missingPackages.append("%s_%s" % (nodeDBPackage, nodeMode))
        if len(missingPackages) == 0:
            dbIsConsistent = True
        return dbIsConsistent, missingPackages

    #def find_package(self, package, mode):
    #    self.logger.debug("find_package method called")
    #    query = """
    #    SELECT COUNT(1)
    #    FROM package
    #    WHERE name = ?
    #    AND opera
    #    self.logger.debug("find_package method exiting")
    #    raise NotImplementedError

    #def find_area(self, area):
    #    raise NotImplementedError

    #def find_source(self, area):
    #    raise NotImplementedError

    #def insert_package(self, package, opMode, opType, currentVersion):
    #    raise NotImplementedError
