import os.path
import argparse
import subprocess
import sys
import os
import time
import errno
import array
import re
#
# Author: Pau Munoz and Andy Marks
# Actualment funciona entenent que el servidor d'openvas es troba a la mateixa maquina
# Utiltizem -w per a especificar un password
# Llegeix IPs que son target d'un arxiu de text

def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return open(arg, 'r')  # handle de l'arxiu obert amb les IPs

def start_process(ip_address, psw):
# El seguent codi crea un TARGET i una tasca per al target, fet aixo activem la tasca. Cada tasca es una IP
# 
   command_line = " omp -w '"+psw+"' --xml=\"<create_target><name>" + ip_address + "</name><hosts>" + ip_address + "</hosts><alive_tests>Consider Alive</alive_tests></create_target>\""
   if debugf == 'yes':
      print command_line
   p = subprocess.Popen([command_line],
       shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


   lines_iterator = iter(p.stdout.readline, b"")
   already_exists = 'No'
   for line in lines_iterator:
       if line.find('status="400"') > 0:
          already_exists = 'Yes'
          p = subprocess.Popen(['omp  -w "4tD)MZ0;f?lA" --get-targets'],
              shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

          lines_iterator = iter(p.stdout.readline, b"")
          for line in lines_iterator:
              if line.find(ip_address) > 0:   
#
# Target ja existeix: retallem la IP de l'output.
#
                 target_id = line[0:36]
       else:
#
# Hem creat el target, agafem el seu ID:  Retallem ID de l'output:
#
          target_id = line[28:64]

#
# Crear la tasca:
#
   command_line = " omp -w '"+psw+"' --xml=\"<create_task><name>" + ip_address + "</name><config id='daba56c8-73ec-11df-a475-002264764cea'/><target id='" + \
       target_id + "'/></create_task>\""
   task_id = ""
   if debugf == 'yes':
      print command_line
   p = subprocess.Popen([command_line],
       shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

   lines_iterator = iter(p.stdout.readline, b"")
   for line in lines_iterator:
       if debugf == 'yes':
          print line
       if line.find('create_task') > 0:
          task_id = line[26:62]
          if debugf == 'yes':
             print task_id

# Output d'exemple:
# <create_task_response id="4a2a53aa-5a80-4900-8128-cee5be30f44b" status_text="OK, resource created" status="201"></create_task_response>

#
# Iniciem la tasca:
#
   command_line = " omp -w '"+psw+"' --xml=\"<start_task task_id='" + task_id + "'/>\""
   if debugf == 'yes':
      print command_line
   p = subprocess.Popen([command_line],
       shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

   lines_iterator = iter(p.stdout.readline, b"")
   already_exists = 'No'
   for line in lines_iterator:
       if debugf == 'yes':
          print line
   return task_id
#
###############################################################
#
#
def get_running_processes(psw):
#
# Nombre de tasques funcionant
#
     command_line = "omp -w '"+psw+"' --get-tasks"
     if debugf == 'yes':
        print command_line
     p = subprocess.Popen([command_line],
         shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
     lines_iterator = iter(p.stdout.readline, b"")
     scans_running = 0
     for line in lines_iterator:
         if debugf == 'yes':
            print line
         if line.find('Running') > 0 or line.find('Requested') > 0:
            scans_running += 1
     return scans_running

def find_between( s, first, last ):
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start )
        return s[start:end]
    except ValueError:
        return ""

def get_report_id(tid, psw):
     getrep=0
     print tid
     command_line =  "omp -w '"+psw+"' -iX '<get_tasks task_id=\""+tid+"\"/>'"
     if debugf == 'yes':
      print command_line
     p = subprocess.Popen([command_line],
       shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

     lines_iterator = iter(p.stdout.readline, b"")
     for line in lines_iterator:
       if debugf == 'yes':
         if "<last_report" in line:
            getrep = 1
            continue
         if getrep == 1:
            getrep = 0
            start = '<report id="'
            end = '">'
            repid = find_between(line,start,end)
            return repid

def get_report_xml(rid, psw):
     print rid
     command_line = "omp -w '"+psw+"' -iX '<get_reports report_id=\""+rid+"\" format_id=\"a994b278-1f62-11e1-96ac-406186ea4fc5\"/>'"
     if debugf == 'yes':
        print command_line
        p = subprocess.Popen([command_line],
        shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        lines_iterator = iter(p.stdout.readline, b"")
     for line in lines_iterator:
        if debugf == 'yes':
          print line

#
#  ---->>> procesos en execucio <<<-----
#
###############################################################
#
# MAIN ()
# El flag de debug serveix per mostrar el que fem en cada moment (outputs)

psw="**********" # PASSWORD D'OPENVAS


parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inputfile", dest="filename", # required=True,
                    help="Arxiu amb llista d'ips a escanejar per defecte: target_addresses.txt", 
                    metavar="FILE",
                    type=lambda x: is_valid_file(parser, x), default='target_addresses.txt')
parser.add_argument("-s", "--sleep", help="Temps per fer sleep entre comprovacions d'estat d'escaneig", 
                    nargs='?', const=10, type=int, default=10)
parser.add_argument("-c", "--concurrent", help="Grau de concurrencia entre escanejos", 
                    nargs='?', const=3, type=int, default=3)
parser.add_argument("-d", "--debug", help="Mostrar informacio de debug",action="store_true")
parser.add_argument("-t", "--target", help="Ip concreta",action="store_true") # alternativa a llegir de fitxer

args = parser.parse_args()

max_concurrent_scans = args.concurrent
sleep_seconds = args.sleep
file = args.filename
if args.debug:
   debugf = 'yes'
else:
   debugf = 'no'
if debugf == 'yes':
   print 'Arxiu: '+str(args.filename)
   print 'Mostrar missatges de debut: '+debugf
   print 'Sleep '+str(sleep_seconds)+' segons entre check.'
   print 'Num escanejos concurrents: '+str(max_concurrent_scans)


ip_array = []

for line in file:
   ip_array.append([str(line).rstrip()])


if max_concurrent_scans > len(ip_array):
   max_concurrent_scans = len(ip_array)

tid=""
running_scans = 0
# ES POT PROGRAMAR UN 'LOT' D'ESCANEJOS, mentre no quedin escanejos en marxa, esperem
while running_scans > 0 or len(ip_array) > 0: 
   if running_scans < max_concurrent_scans:
      number_to_kickoff = max_concurrent_scans - running_scans
      if debugf == 'yes':
         print number_to_kickoff
      if len(ip_array) > 0:
         for startloop in range(0,number_to_kickoff):
            ip_address = ip_array[0]
            if debugf == 'yes':
               print ip_array[0]
            del ip_array[0]
            tid = start_process((ip_address)[0],psw)

   running_scans = get_running_processes(psw)
   print 'Running scans: '+str(running_scans)
  # Sleep per no sobrecarregar el sistema fent comprovacions tota l'estona
   time.sleep(sleep_seconds)
print 'All scans complete.'
print tid
rid = get_report_id(tid,psw)
get_report_xml(rid,psw)