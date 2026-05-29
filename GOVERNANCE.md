# CollectOSS Project Governance

CollectOSS is dedicated to building and improving a data collection, transformation, and serving backend for open source contributor activity. CollectOSS will operate as a project within the CHAOSS Organization, which is a member of the Linux Foundation. This governance explains how the project is run.

- [Values](#values)
- [Maintainers](#maintainers)
- [Becoming a Maintainer](#becoming-a-maintainer)
- [Meetings](#meetings)
- [CHAOSS Resources](#CHAOSS-resources)
- [Code of Conduct Enforcement](#code-of-conduct)
- [Security Response Team](#security-response-team)
- [Voting](#voting)
- [Modifications](#modifying-this-charter)

## Values

The CollectOSS and its leadership embrace the following values:

* Openness: Communication and decision-making happens in the open and is discoverable for future
  reference. As much as possible, all discussions and work take place in public
  forums and open repositories.

* Fairness: All stakeholders have the opportunity to provide feedback and submit
  contributions, which will be considered on their merits.

* Inclusivity: We innovate through different perspectives and skill sets, which
  can only be accomplished in a welcoming and respectful environment.

* Participation: Responsibilities within the project are earned through
  participation, and there is a clear path up the contributor ladder into leadership
  positions.

## Maintainers

The current maintainers can be found in [MAINTAINERS.md](./MAINTAINERS.md).  Maintainers collectively manage the project's resources and contributors.

CollectOSS Maintainers have merge approval rights to the [project GitHub repository](https://github.com/chaoss/collectoss) and all other CollectOSS project repositories.

This privilege is granted with some expectation of responsibility: maintainers
are people who care about the CollectOSS project and want to help it grow and
improve. A maintainer is not just someone who can make changes, but someone who
has demonstrated their ability to collaborate with the team, get the most
knowledgeable people to review code and docs, contribute high-quality code, and
follow through to fix issues (in code or tests).

A maintainer is a contributor to the project's success and a citizen helping
the project succeed.

The collective team of all Maintainers is known as the Maintainer Council, which
is the governing body for the project.

### Becoming a Maintainer

To become a Maintainer you need to demonstrate the following:

  * commitment to the project:
    * participate in discussions, contributions, code and documentation reviews
      for 6 months or more,
    * perform reviews for at least 4 non-trivial pull requests,
    * contribute at least 3 non-trivial pull requests and have them merged,
  * ability to write quality code and/or documentation,
  * ability to collaborate with the team,
  * understanding of how the team works (policies, processes for testing and code review, etc),
  * understanding of the project's code base and coding and documentation style,
  * dedication to maintaining CollectOSS as a shared project for the CHAOSS community.

A new Maintainer must be proposed by an existing Maintainer by posting an issue in the project repository. A simple majority vote of existing Maintainers approves the application.  Maintainers nominations will be evaluated without prejudice to employer or demographics.

Maintainers who are selected will be granted the necessary GitHub rights,
and invited to the private maintainer slack channel.

### Removing a Maintainer

Maintainers may resign at any time if they feel that they will not be able to
continue fulfilling their project duties.

Maintainers may also be removed after being inactive, failure to fulfill their 
Maintainer responsibilities, violating the Code of Conduct, or other reasons.
Inactivity is defined as a period of very low or no activity in the project 
for a year or more, with no definite schedule to return to full Maintainer 
activity.

A Maintainer may be removed at any time by a 2/3 vote of the remaining maintainers.

Depending on the reason for removal, a Maintainer may be converted to Emeritus
status.  Emeritus Maintainers will still be consulted on some project matters,
and can be rapidly returned to Maintainer status if their availability changes.

## Meetings

Time zones permitting, Maintainers are expected to participate in the public
developer meeting, which occurs every two weeks according to the CHAOSS calendar.  

Maintainers will also have closed meetings in order to discuss security reports
or reports from the CHAOSS Code of Conduct Committee.  Such meetings should be scheduled by any Maintainer on receipt of a security issue or CoCC message.  All current Maintainers must be invited to such closed meetings, except for any Maintainer who is accused of a CoC violation.

## CHAOSS Resources

Any Maintainer may suggest a request for CHAOSS resources, either in an issue, or during a meeting.  A simple majority of Maintainers approves the request.  The Maintainers may also choose to delegate working with CHAOSS to non-Maintainer community members, who will then be added to the [MAINTAINERS.md file](./MAINTAINERS.md) with that special status.

## Code of Conduct Committee

The CollectOSS project adheres to the [CHAOSS Code of Conduct](https://chaoss.community/code-of-conduct/)(CoC).  As such, community members needing to report a violation of the CoC should report it directly to the CHAOSS Code Of Conduct Committee (CoCC).

The Maintainers will work with the CoCC on any reports which require action by the project. 

## Security Response Team

The Maintainers will appoint a Security Response Team to handle security reports.
This committee may simply consist of the Maintainer Council themselves.  If this
responsibility is delegated, the Maintainers will appoint a team of at least two 
contributors to handle it.  The Maintainers will review who is assigned to this
at least once a year.

The Security Response Team is responsible for handling all reports of security
holes and breaches according to the [security policy](./SECURITY.md).

## Voting

While most business in CollectOSS is conducted by "[lazy consensus](https://community.apache.org/committers/lazyConsensus.html)", 
periodically the Maintainers may need to vote on specific actions or changes.
A vote can be taken on the project's public Slack channel (#wg-collectoss-8knot in the [CHAOSS Slack](https://chaoss.community/kb-getting-started/)) or 
the private Maintainer Slack channel for security or conduct matters.  
Votes may also be taken at the biweely developer meeting.  Any Maintainer may
demand a vote be taken.

Most votes require a simple majority of all Maintainers to succeed, except where
otherwise noted.  Two-thirds majority votes mean at least two-thirds of all 
existing maintainers.

## Transitional Period

There will be a Transitional Period for six to eight months after the CollectOSS project is launched.  During that transitional period, the project governance will be modified in the following ways in order to build a new Maintainer Council.

The project will be governed by the [Transitional Maintainers](./MAINTAINERS.md), who may or may not meet the standard qualifications for a Maintainer. 
* The Transitional Maintainers will be seeking to appoint new Maintainers based on an optimitistic and flexible evaluation of their contributions during the first months of the project.  This will generally include "crediting" contributors for contributions made to the Augur project.  
* Newly appointed Maintainers do not need to meet the full qualifications for Maintainer above (particularly the 6 month requirement), and will be approved by a fast-track process.

The following will happen at the end of the Transitional Period:

1. The Maintainers to date will vote to end the Transition.  
2. The Maintainers will update the Maintainer requirements based on the early project experience.
3. Any Transitional Maintainers who do not qualify as, or do not wish to be, long-term Maintainers will step down, and the remaining ones will be converted to long-term Maintainers.  
4. This section will then be removed from the Governance.

## Modifying this Charter

Changes to this Governance and its supporting documents may be approved by 
a 2/3 vote of the Maintainers.

This governance document was created based on the template available at https://github.com/cncf/project-template/blob/main/GOVERNANCE-maintainer.md
