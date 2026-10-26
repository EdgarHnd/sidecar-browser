#import <Foundation/Foundation.h>
#include <cassert>
#include "../native/sidecar_update_feed.h"

int main() {
  @autoreleasepool {
    NSString* key = [[NSMutableData dataWithLength:32] base64EncodedStringWithOptions:0];
    NSString* feed = @"https://github.com/example/sidecar/releases/latest/download/appcast.xml";
    NSMutableDictionary* info = [@{@"SidecarUpdateFeedURL": feed,
                                  @"SUPublicEDKey": key} mutableCopy];
    assert([sidecar::UpdateFeedURL(info) isEqualToString:feed]);
    for (NSString* invalid in @[@"http://example.com/appcast.xml",
                                @"file:///tmp/appcast.xml",
                                @"https://user:password@example.com/appcast.xml",
                                @"https://example.com/appcast.xml#fragment",
                                @"https:///", @""]) {
      info[@"SidecarUpdateFeedURL"] = invalid;
      assert(sidecar::UpdateFeedURL(info) == nil);
    }
    info[@"SidecarUpdateFeedURL"] = @42;
    assert(sidecar::UpdateFeedURL(info) == nil);
    info[@"SidecarUpdateFeedURL"] = feed;
    for (id invalid in @[@"", @"not-base64", @42]) {
      info[@"SUPublicEDKey"] = invalid;
      assert(sidecar::UpdateFeedURL(info) == nil);
    }
    [info removeObjectForKey:@"SUPublicEDKey"];
    assert(sidecar::UpdateFeedURL(info) == nil);
    assert(sidecar::UpdateFeedURL(@{}) == nil);
    puts("Native updater feed validation passed.");
  }
}
