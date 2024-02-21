# Catalog

These files are used by the values files in the [gitops-repo](https://github.com/bcgov-c/tenant-gitops-f5ff48). They contain the seed data for our backstage instance entities.

## Troubleshooting

### Entity not picked up

#### Scenario

We had an instance where changes to the entity's title were not picked up. This happened because there were duplicate entries for the entity in the seed file. The entries pointed to different locations (branches). Deleting the wrong entry did NOT result in the correct seed being picked up.

#### Resolution

After removing the wrong entry and the title still was not updated, we did the following:

* Removed the correct entry from the seed file
* Committed to repo
* Restarted deployment on OpenShift (scale pod to 0, and then backup)
* Put correct entry back into seed file
* Committed to repo
* Restarted deployment on OpenShift (scale pod to 0, and then backup)
* Entity showed up as expected

Note: It may take several minutes (I've noticed 20 minutes but could be more) for a change to be picked up. So after making the change, wait to see if it is picked up. Refer to [The Life of an Entity](https://backstage.io/docs/features/software-catalog/life-of-an-entity) about the steps an entity goes through to be processed.

#### Notes

If you encounter this scenario and the above does not work, the following maybe helpful:

* [The Life of an Entity](https://backstage.io/docs/features/software-catalog/life-of-an-entity)
* [Invalid Catalog Entries get stuck in refresh loop](https://github.com/backstage/backstage/issues/12333)
* [Bug Report: Renamed entities are not being picked up after renaming and deleting the orphan](https://github.com/backstage/backstage/issues/19069)
* [Bug Report: Entities not deleted/orphaned properly if they were in an error state before being deleted](https://github.com/backstage/backstage/issues/15521)