#!/usr/bin/env python
#-*- coding: utf-8 -*-

"""
This module describes the Model used by the stats database. It is implemented
using python's sqlalchemy package, which offers an abstraction between the 
actual DBMS used and the code.

The module is currently using sqlite as a DBMS backend, but this could
theoretically be changed very easily, by altering the engine variable.
"""

# TODO
# - The insert_process method of the G2DatabaseManager class is huge. It 
# should be broken down into smaller pieces.

import logging
import os
import datetime as dt

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relation
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import Column, Integer, String, ForeignKey, create_engine, DateTime, Boolean, and_, ForeignKeyConstraint

import packagecreator as pc
import utilities

Base = declarative_base()
Session = sessionmaker()

class PaFiPr(Base):
    __tablename__ = 'pa_fi_pr'
    __table_args__ = (
        ForeignKeyConstraint(['package_id', 'filetype_id'],['pa_fi.package_id', 'pa_fi.filetype_id']),
        {}
    )
    package_id = Column(Integer, primary_key=True)
    filetype_id = Column(Integer, primary_key=True)
    process_id = Column(Integer, ForeignKey('process.id'), primary_key=True)
    fileTimeslot = Column(DateTime, index=True)
    fileArea = Column(String)
    fileSource = Column(String)
    expectedFiles = Column(Integer)
    numActualFiles = Column(Integer)
    process = relation("Process", backref="pafiprs")

    def __init__(self, g2package, g2file, numFiles):
        self.fileTimeslot = g2file.timeslotDT
        self.fileArea = g2file.sourceObj.area
        self.fileSource = g2file.sourceObj.source 
        self.expectedFiles = g2file.numFiles
        self.numActualFiles = numFiles

    def __repr__(self):
        return "<%s (package: %s, file: %s)>" % (self.__class__.__name__, self.package_id, self.filetype_id)


class PaFi(Base):
    __tablename__ = 'pa_fi'

    filetype_id = Column(Integer, ForeignKey('filetype.id'), primary_key=True)
    package_id = Column(Integer, ForeignKey('package.id'), primary_key=True)
    fileRole = Column(String)
    modeVersion = Column(String)
    ftype = relation("Filetype", backref="pafis")
    pafiprs = relation(PaFiPr, backref="pafi")

    def __init__(self, fileRole, modeVersion):
        self.fileRole = fileRole
        self.modeVersion = modeVersion

    def __repr__(self):
        return "<%s (package: %s, file: %s)>" % (self.__class__.__name__, self.package_id, self.filetype_id)


class Package(Base):
    __tablename__ = 'package'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    mode = Column(String)
    pafis = relation(PaFi, backref="package")

    def __init__(self, g2Package):
        self.name = g2Package.name
        self.mode = g2Package.mode

    def __repr__(self):
        return "<%s (%s, %s)>" % (self.__class__.__name__, self.name, self.mode)


class Filetype(Base):
    __tablename__ = 'filetype'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    ftype = Column(String)

    def __init__(self, g2File):
        """
        Inputs:
            g2file - A G2File instance
        """

        self.name = g2File.name
        self.ftype = g2File.type

    def __repr__(self):
        return "<%s (%s, %s)>" % (self.__class__.__name__, self.name, self.ftype)


class Process(Base):
    __tablename__ = 'process'

    id = Column(Integer, primary_key=True)
    timeslot = Column(DateTime, index=True)
    processing_mode = Column(String, nullable=False)
    status = Column(Boolean, nullable=False) 
    pack_area = Column(String, nullable=False)
    pack_version = Column(String, nullable=False)
    pack_source = Column(String, nullable=False)
    # this relation is not necessary since it can be implied from the model
    # easily. To get a process' package: > process.pafiprs[0].pafi.package
    package_id = Column(Integer, ForeignKey('package.id'))
    package = relation(Package, backref="processes", primaryjoin="package.c.id==process.c.package_id")

    def __init__(self, g2package, status, processingMode):
        self.status = status
        self.processing_mode = processingMode
        self.timeslot = g2package.timeslotDT
        self.pack_version = g2package.version
        self.pack_source = g2package.sourceObj.source
        self.pack_area = g2package.sourceObj.area

    def __repr__(self):
        try:
            pack = self.pafiprs[0].pafi.package
            params = (self.__class__.__name__, pack.name, pack.mode, self.timeslot, self.status)
        except IndexError:
            params = (self.__class__.__name__, None, None, self.timeslot, self.status)
        return "<%s (package: %s, mode: %s, timeslot: %s, status: %s)>" % params


class G2DatabaseManager(object):
    """
    ...
    """

    def __init__(self, databasePath):
        self.logger = logging.getLogger()
        self.engine = create_engine("sqlite:///%s" % databasePath)
        Base.metadata.create_all(self.engine)
        Session.configure(bind=self.engine)
        self.Session = Session

    def insert_process(self, g2Package, status, opType):
        """
        Insert or update a given process, along with its accompanying
        package and filetypes.
        """

        session = self.Session()
        try:
            # try to find the package in the database
            package = session.query(Package).filter(\
                      Package.name == g2Package.name).filter(\
                      Package.mode == g2Package.mode).one()
            logging.debug("Found this package in the database")
        except NoResultFound:
            logging.debug("This package is new in the database")
            package = Package(g2Package)
        try:
            proc = session.query(Process).join(Package).filter(\
                   Package.name == g2Package.name).filter(\
                   Package.mode == g2Package.mode).filter(\
                   Process.timeslot == g2Package.timeslotDT).one()
            logging.debug("Found this process in the database")
        except NoResultFound:
            logging.debug("This process is new in the database")
            proc = Process(g2Package, status, opType)
            proc.package = package
                
        session.add(package)
        session.add(proc)

        for f in g2Package.inputs + g2Package.outputs:
            try:
                # try to find this filetype in the database
                ftype = session.query(Filetype).filter(\
                        Filetype.name == f.name).one()
                logging.debug("Found this Filetype in the database")
            except NoResultFound:
                logging.debug("This Filetype is new in the database")
                ftype = Filetype(f)
            try:
                # try to find this combination of filetype, package and mode version in the database
                pafi = session.query(PaFi).filter(\
                       PaFi.filetype_id == ftype.id).filter(\
                       PaFi.package_id == package.id).filter(\
                       PaFi.modeVersion == g2Package.version).filter(\
                       PaFi.fileRole == f.role).one()
                logging.debug("Found this pafi in the database")
            except NoResultFound:
                logging.debug("This pafi is new in the database")
                pafi = PaFi(f.role, g2Package.version)
                pafi.ftype = ftype
                pafi.package = package
            try:
                # try to find this combination of filetype, package, mode and process in the db
                pafipr = session.query(PaFiPr).join(Process).join(\
                         Package).filter(\
                         Package.id == package.id).filter(\
                         Process.timeslot == proc.timeslot).filter(\
                         PaFiPr.filetype_id == ftype.id).one()
                logging.debug("Found this pafipr in the database")
            except NoResultFound:
                logging.debug("This pafipr is new in the database")
                pafipr = PaFiPr(g2Package, f, 0)
                pafipr.process = proc
                pafipr.pafi = pafi

            session.add(pafi)
            session.add(ftype)
            session.add(pafipr)
        session.commit()
        session.close()

    # Haven't decided if implementing database records of disseminated data 
    # is worth the confusion

    #def _find_g2files(self, g2Package):
    #    """
    #    ...
    #    """

    #    if g2Package.__class__.__name__ == "G2Disseminator":
    #        g2Files = []
    #        for itemDict in g2Package.dissPackages:
    #            pack = itemDict["package"]
    #            g2Files += pack.outputs
    #    else:
    #        g2Files = g2Package.inputs + g2Package.outputs


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # fake sms variables
    ymd = '20110201'
    hour = '22'
    algorithmMode = 'lrit_mtsat'
    algorithmVersion = '1.0'
    area = 'MTSAT-Disk'
    packageName = 'fetchData'
    suiteName = 'G2NRT'
    opStatus = 'OPERATIONAL' # <- not needed?
    opType = 'NRT'

    databasePath = utilities.get_new_settings()["database"]
    databaseDir = os.path.dirname(databasePath)
    if not os.path.isdir(databaseDir):
        os.makedirs(databaseDir)
    engine = create_engine("sqlite:///%s" % databasePath)
    logging.debug("Saving database...")
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)
    session = Session()

    # creating a normal G2Package
    logging.debug("Creating a G2Package object...")
    timeslot = ymd + hour + '00'
    pack = pc.package_creator(packageName, algorithmMode, timeslot, area, 
                              opStatus, suiteName, algorithmVersion)
    processStatus = True

    # inserting data in the database
    try:
        # try to find the package in the database
        package = session.query(Package).filter(\
                  Package.name == pack.name).filter(\
                  Package.mode == pack.mode).one()
        logging.debug("Found this package in the database")
    except NoResultFound:
        logging.debug("This package is new in the database")
        package = Package(pack)
    try:
        proc = session.query(Process).join(Package).filter(\
               Package.name == pack.name).filter(\
               Package.mode == pack.mode).filter(\
               Process.timeslot == dt.datetime.strptime(\
               timeslot, "%Y%m%d%H%M")).one()
        #proc = session.query(Process).filter(Process.pack_area == 'dummy').one() #<- just filler code
        logging.debug("Found this process in the database")
    except NoResultFound:
        logging.debug("This process is new in the database")
        proc = Process(pack, processStatus, opType)
        proc.package = package
                
    session.add(package)
    session.add(proc)
    for f in pack.inputs + pack.outputs:
        try:
            # try to find this filetype in the database
            ftype = session.query(Filetype).filter(Filetype.name == f.name).one()
            logging.debug("Found this Filetype in the database")
        except NoResultFound:
            logging.debug("This Filetype is new in the database")
            ftype = Filetype(f)
        try:
            # try to find this combination of filetype, package and mode version in the database
            pafi = session.query(PaFi).filter(\
                   PaFi.filetype_id == ftype.id).filter(\
                   PaFi.package_id == package.id).filter(\
                   PaFi.modeVersion == pack.version).filter(
                   PaFi.fileRole == f.role).one()
            logging.debug("Found this pafi in the database")
        except NoResultFound:
            logging.debug("This pafi is new in the database")
            pafi = PaFi(f.role, pack.version)
            pafi.ftype = ftype
            pafi.package = package
        try:
            # try to find this combination of filetype, package, mode and process in the db
            pafipr = session.query(PaFiPr).join(Process).join(Package).filter(\
                     Package.id == package.id).filter(\
                     Process.timeslot == proc.timeslot).filter(\
                     PaFiPr.filetype_id == ftype.id).one()
            logging.debug("Found this pafipr in the database")
        except NoResultFound:
            logging.debug("This pafipr is new in the database")
            pafipr = PaFiPr(pack, f, 0)
            pafipr.process = proc
            pafipr.pafi = pafi

        session.add(pafi)
        session.add(ftype)
        session.add(pafipr)
    pack.clean_up()
    session.commit()
