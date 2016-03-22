# Open Desktop Ratings Serice

A Flask web service for submitting application reviews

## Concept

Choosing an application to install is hard when there are lots of
possible projects matching a specific search term.
We already list applications based on the integration level and with
useful metrics like "is it translated in my language" and this makes
sure that high quality applications are listed near the top of the results.
For more information about an application we often want a more balanced
view than the PR speak or unfounded claims of the upstream project.
This is where user-contributed reviews come in.

To get a user to contribute a review (which takes time) we need to make
the process as easy as possible.
Making the user create a user account on yet-another-webservice will
make this much harder and increase the barrier to participation to the
point that very few people would contribute reviews.
If anonymous reviewing does not work the plan is to use some kind of
attestation service so you can use a GMail or Facebook for confirming
your identity.
At this point I'm hoping people will just be nice to each other and not
abuse the service although this reviewing facility will go away if it
starts being misused.

**NOTE: The API will change, and without warning. Caveat Emptor!**

## API Design

Designing an anonymous service is hard when you have to be resilient
against a socially awkward programmer with specific political ideologies.
If you don't know any people that match this description you have
obviously never been subscribed to fedora-devel or memo-list.

### Privacy

Obviously when contacting a web service you share your IP address.
This isn't enough to uniquely identify a machine and user, which we
want for the following reasons:

 * Allowing users to retract only their own reviews
 * Stopping users up or down-voting the same review multiple times

A compromise would be to send a hash of two things that identify the
user and machine.
In GNOME Software we're using a SHA1 hash of the machine-id and the
UNIX username along with a salt, although this "user_id" is only
specified as a string and the format is not checked.

When the client requests some comments and sets the `user_id` hash as
generated above the returned reviews have an additional key called
`user_key`.
The user key is a SHA1 hash of the user ID sent in the request, along
with the application ID and also a secret value.
It should be impossible to generate a `user_key` from a `user_id`
without first requesting the reviews from the server.
This prevents an end user just writing a trivial python program that
can upvote a specific comment.

To then vote or remove a specific review you need to specify the
`user_key` and `user_id` values along with the `review_id`.

## Moderation

For projects like RHEL where we care very much what comments are shown
to paying customers we definitely want reviews to be pre-approved and
checked before showing to customers.
For distros like Fedora we don't have this luxury and so we're going to
rely on the community to self-regulate reviews.
Reviews are either up-voted or down-voted according how useful they are
along with the nuclear option of marking the review as abusive.

### Choosing Reviews for each Application

By specifying the users current locale we can sort the potential
application reviews according to a heuristic that we're still working on.
Generally we want to prefer useful reviews in the users locale and hide
ones that have been marked as abusive, and we also want to indicate the
users self-review so they can remove it later if required.
We also want to prioritize reviews for the current application version
compared to really old versions of these applications.

## I have a question

Email me or grab me on IRC (`hughsie@freenode`).
