// Copyright (c) 2026 Sidecar contributors.
// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this file,
// You can obtain one at https://mozilla.org/MPL/2.0/.

#ifndef BRAVE_BROWSER_MAC_SIDECAR_UPDATE_FEED_H_
#define BRAVE_BROWSER_MAC_SIDECAR_UPDATE_FEED_H_

#import <Foundation/Foundation.h>

namespace sidecar {

inline NSString* UpdateFeedURL(NSDictionary* info) {
  id feed = info[@"SidecarUpdateFeedURL"];
  id public_key = info[@"SUPublicEDKey"];
  if (![feed isKindOfClass:[NSString class]] ||
      ![public_key isKindOfClass:[NSString class]]) {
    return nil;
  }
  NSURLComponents* url = [NSURLComponents componentsWithString:feed];
  NSData* key = [[NSData alloc] initWithBase64EncodedString:public_key options:0];
  if (![url.scheme isEqualToString:@"https"] || !url.host.length ||
      url.user || url.password || url.fragment || key.length != 32) {
    return nil;
  }
  return feed;
}

}  // namespace sidecar

#endif  // BRAVE_BROWSER_MAC_SIDECAR_UPDATE_FEED_H_
