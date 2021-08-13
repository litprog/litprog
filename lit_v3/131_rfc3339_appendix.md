## Appendix

### Appendix A: ISO 8601 Collected ABNF

This information is based on the 1988 version of ISO 8601.  There may be some changes in the 2000 revision.

ISO 8601 does not specify a formal grammar for the date and time formats it defines.  The following is an attempt to create a formal grammar from ISO 8601.  This is informational only and may contain errors.  ISO 8601 remains the authoritative reference.

Note that due to ambiguities in ISO 8601, some interpretations had to be made.  First, ISO 8601 is not clear if mixtures of basic and extended format are permissible.  This grammar permits mixtures. ISO 8601 is not clear on whether an hour of 24 is permissible only if minutes and seconds are 0.  This assumes that an hour of 24 is permissible in any context.  Restrictions on date-mday in section 5.7 apply.  ISO 8601 states that the "T" may be omitted under some circumstances.  This grammar requires the "T" to avoid ambiguity. ISO 8601 also requires (in section 5.3.1.3) that a decimal fraction be proceeded by a "0" if less than unity.  Annex B.2 of ISO 8601 gives examples where the decimal fractions are not preceded by a "0". This grammar assumes section 5.3.1.3 is correct and that Annex B.2 is in error.

```
   date-century    = 2DIGIT  ; 00-99
   date-decade     =  DIGIT  ; 0-9
   date-subdecade  =  DIGIT  ; 0-9
   date-year       = date-decade date-subdecade
   date-fullyear   = date-century date-year
   date-month      = 2DIGIT  ; 01-12
   date-wday       =  DIGIT  ; 1-7  ; 1 is Monday, 7 is Sunday
   date-mday       = 2DIGIT  ; 01-28, 01-29, 01-30, 01-31 based on
                             ; month/year
   date-yday       = 3DIGIT  ; 001-365, 001-366 based on year
   date-week       = 2DIGIT  ; 01-52, 01-53 based on year

   datepart-fullyear = [date-century] date-year ["-"]
   datepart-ptyear   = "-" [date-subdecade ["-"]]
   datepart-wkyear   = datepart-ptyear / datepart-fullyear

   dateopt-century   = "-" / date-century
   dateopt-fullyear  = "-" / datepart-fullyear
   dateopt-year      = "-" / (date-year ["-"])
   dateopt-month     = "-" / (date-month ["-"])
   dateopt-week      = "-" / (date-week ["-"])
   datespec-full     = datepart-fullyear date-month ["-"] date-mday
   datespec-year     = date-century / dateopt-century date-year
   datespec-month    = "-" dateopt-year date-month [["-"] date-mday]
   datespec-mday     = "--" dateopt-month date-mday
   datespec-week     = datepart-wkyear "W"
                       (date-week / dateopt-week date-wday)
   datespec-wday     = "---" date-wday
   datespec-yday     = dateopt-fullyear date-yday

   date              = datespec-full / datespec-year
                       / datespec-month /
   datespec-mday / datespec-week / datespec-wday / datespec-yday
```

Time:

```
   time-hour         = 2DIGIT ; 00-24
   time-minute       = 2DIGIT ; 00-59
   time-second       = 2DIGIT ; 00-58, 00-59, 00-60 based on
                              ; leap-second rules
   time-fraction     = ("," / ".") 1*DIGIT
   time-numoffset    = ("+" / "-") time-hour [[":"] time-minute]
   time-zone         = "Z" / time-numoffset

   timeopt-hour      = "-" / (time-hour [":"])
   timeopt-minute    = "-" / (time-minute [":"])

   timespec-hour     = time-hour [[":"] time-minute [[":"] time-second]]
   timespec-minute   = timeopt-hour time-minute [[":"] time-second]
   timespec-second   = "-" timeopt-minute time-second
   timespec-base     = timespec-hour / timespec-minute / timespec-second

   time              = timespec-base [time-fraction] [time-zone]

   iso-date-time     = date "T" time
```

Durations:

```
   dur-second        = 1*DIGIT "S"
   dur-minute        = 1*DIGIT "M" [dur-second]
   dur-hour          = 1*DIGIT "H" [dur-minute]
   dur-time          = "T" (dur-hour / dur-minute / dur-second)
   dur-day           = 1*DIGIT "D"
   dur-week          = 1*DIGIT "W"
   dur-month         = 1*DIGIT "M" [dur-day]
   dur-year          = 1*DIGIT "Y" [dur-month]
   dur-date          = (dur-day / dur-month / dur-year) [dur-time]

   duration          = "P" (dur-date / dur-time / dur-week)
```

Periods:

```
   period-explicit   = iso-date-time "/" iso-date-time
   period-start      = iso-date-time "/" duration
   period-end        = duration "/" iso-date-time

   period            = period-explicit / period-start / period-end
```


### Appendix B: Day of the Week

The following is a sample C subroutine loosely based on Zeller's Congruence [Zeller] which may be used to obtain the day of the week for dates on or after 0000-03-01:

```c
char *day_of_week(int day, int month, int year)
{
   int cent;
   char *dayofweek[] = {
      "Sunday", "Monday", "Tuesday", "Wednesday",
      "Thursday", "Friday", "Saturday"
   };

   /* adjust months so February is the last one */
   month -= 2;
   if (month < 1) {
      month += 12;
      --year;
   }
   /* split by century */
   cent = year / 100;
   year %= 100;
   return (dayofweek[((26 * month - 2) / 10 + day + year
                     + year / 4 + cent / 4 + 5 * cent) % 7]);
}
```

### Appendix C: Leap Years

Here is a sample C subroutine to calculate if a year is a leap year:

```c
/* This returns non-zero if year is a leap year.  Must use 4 digit
   year.
 */
int leap_year(int year)
{
    return (year % 4 == 0 && (year % 100 != 0 || year % 400 == 0));
}
```


### Appendix D: Leap Seconds

Information about leap seconds can be found at: <http://tycho.usno.navy.mil/leapsec.html>.  In particular, it notes that:

> The decision to introduce a leap second in UTC is the
> responsibility of the International Earth Rotation Service (IERS).
> According to the CCIR Recommendation, first preference is given to
> the opportunities at the end of December and June, and second
> preference to those at the end of March and September.

When required, insertion of a leap second occurs as an extra second at the end of a day in UTC, represented by a timestamp of the form `YYYY-MM-DDT23:59:60Z`.  A leap second occurs simultaneously in all time zones, so that time zone relationships are not affected.  See section 5.8 for some examples of leap second times.

The following table is an excerpt from the table maintained by the United States Naval Observatory.  The source data is located at:

`<ftp://maia.usno.navy.mil/ser7/tai-utc.dat>`

This table shows the date of the leap second, and the difference between the time standard TAI (which isn't adjusted by leap seconds) and UTC after that leap second.

```
   UTC Date  TAI - UTC After Leap Second
   --------  ---------------------------
   1972-06-30     11
   1972-12-31     12
   1973-12-31     13
   1974-12-31     14
   1975-12-31     15
   1976-12-31     16
   1977-12-31     17
   1978-12-31     18
   1979-12-31     19
   1981-06-30     20
   1982-06-30     21
   1983-06-30     22
   1985-06-30     23
   1987-12-31     24
   1989-12-31     25
   1990-12-31     26
   1992-06-30     27
   1993-06-30     28
   1994-06-30     29
   1995-12-31     30
   1997-06-30     31
   1998-12-31     32
```


## Acknowledgements

The following people provided helpful advice for an earlier incarnation of this document:  Ned Freed, Neal McBurnett, David Keegel, Markus Kuhn, Paul Eggert and Robert Elz.  Thanks are also due to participants of the IETF Calendaring/Scheduling working group mailing list, and participants of the time zone mailing list.

The following reviewers contributed helpful suggestions for the present revision: Tom Harsch, Markus Kuhn, Pete Resnick, Dan Kohn. Paul Eggert provided many careful observations regarding the subtleties of leap seconds and time zone offsets.  The following people noted corrections and improvements to earlier drafts: Dr John Stockton, Jutta Degener, Joe Abley, and Dan Wing.


## Full Copyright Statement

Copyright (C) The Internet Society (2002).  All Rights Reserved.

This document and translations of it may be copied and furnished to others, and derivative works that comment on or otherwise explain it or assist in its implementation may be prepared, copied, published and distributed, in whole or in part, without restriction of any kind, provided that the above copyright notice and this paragraph are included on all such copies and derivative works.  However, this document itself may not be modified in any way, such as by removing the copyright notice or references to the Internet Society or other Internet organizations, except as needed for the purpose of developing Internet standards in which case the procedures for copyrights defined in the Internet Standards process must be followed, or as required to translate it into languages other than English.

The limited permissions granted above are perpetual and will not be revoked by the Internet Society or its successors or assigns.

   This document and the information contained herein is provided on an
   "AS IS" basis and THE INTERNET SOCIETY AND THE INTERNET ENGINEERING
   TASK FORCE DISCLAIMS ALL WARRANTIES, EXPRESS OR IMPLIED, INCLUDING
   BUT NOT LIMITED TO ANY WARRANTY THAT THE USE OF THE INFORMATION
   HEREIN WILL NOT INFRINGE ANY RIGHTS OR ANY IMPLIED WARRANTIES OF
   MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE.
