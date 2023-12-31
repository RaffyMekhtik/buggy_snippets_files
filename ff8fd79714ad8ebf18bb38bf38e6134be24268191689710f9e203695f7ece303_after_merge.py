def main():
    """Reports the state of the toil.
    """
    
    ##########################################
    #Construct the arguments.
    ##########################################  
    
    parser = getBasicOptionParser()
    
    parser.add_argument("jobStore", type=str,
                        help="The location of a job store that holds the information about the "
                             "workflow whose status is to be reported on." + jobStoreLocatorHelp)
    
    parser.add_argument("--verbose", dest="verbose", action="store_true",
                      help="Print loads of information, particularly all the log files of \
                      jobs that failed. default=%(default)s",
                      default=False)
    
    parser.add_argument("--failIfNotComplete", dest="failIfNotComplete", action="store_true",
                      help="Return exit value of 1 if toil jobs not all completed. default=%(default)s",
                      default=False)
    parser.add_argument("--version", action='version', version=version)
    options = parseBasicOptions(parser)
    logger.info("Parsed arguments")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    
    ##########################################
    #Do some checks.
    ##########################################
    
    logger.info("Checking if we have files for Toil")
    assert options.jobStore is not None

    ##########################################
    #Survey the status of the job and report.
    ##########################################  
    
    jobStore = Toil.resumeJobStore(options.jobStore)
    try:
        rootJob = jobStore.loadRootJob()
    except JobException:
        print('The root job of the job store is absent, the workflow completed successfully.',
              file=sys.stderr)
        sys.exit(0)
    
    toilState = ToilState(jobStore, rootJob )

    # The first element of the toilState.updatedJobs tuple is the jobWrapper we want to inspect
    totalJobs = set(toilState.successorCounts.keys()) | \
                {jobTuple[0] for jobTuple in toilState.updatedJobs}

    failedJobs = [ job for job in totalJobs if job.remainingRetryCount == 0 ]

    print('There are %i active jobs, %i parent jobs with children, and %i totally failed jobs '
          'currently in %s.' % (len(toilState.updatedJobs), len(toilState.successorCounts),
                                len(failedJobs), options.jobStore), file=sys.stderr)
    
    if options.verbose: #Verbose currently means outputting the files that have failed.
        for job in failedJobs:
            if job.logJobStoreFileID is not None:
                with job.getLogFileHandle(jobStore) as logFileHandle:
                    logStream(logFileHandle, job.jobStoreID, logger.warn)
            else:
                print('Log file for job %s is absent.' % job.jobStoreID, file=sys.stderr)
        if len(failedJobs) == 0:
            print('There are no failed jobs to report.', file=sys.stderr)
    
    if (len(toilState.updatedJobs) + len(toilState.successorCounts)) != 0 and \
        options.failIfNotComplete:
        sys.exit(1)