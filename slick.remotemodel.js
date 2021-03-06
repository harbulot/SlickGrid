(function($) {
	/***
	 * A sample AJAX data store implementation.
	 * Right now, it's hooked up to load all Apple-related Digg stories, but can
	 * easily be extended to support and JSONP-compatible backend that accepts paging parameters.
	 */
	function RemoteModel() {
		// private
		var PAGESIZE = 50;
		var data = {length:0};
		var sortcol = null;
		var sortdir = 1;
		var h_request = null;
		var req = null; // ajax request
		var urlBuilder = null;
		var responseItemListName = "items";

		// events
		var onDataLoading = new Slick.Event();
		var onDataLoaded = new Slick.Event();


		function init() {
		}


		function isDataLoaded(from,to) {
			for (var i=from; i<=to; i++) {
				if (data[i] == undefined || data[i] == null)
					return false;
			}

			return true;
		}


		function clear() {
			for (var key in data) {
				delete data[key];
			}
			data.length = 0;
		}


		function ensureData(from,to) {
			if (req) {
				req.abort();
				for (var i=req.fromPage; i<=req.toPage; i++)
					data[i*PAGESIZE] = undefined;
			}

			if (from < 0)
				from = 0;

			var fromPage = Math.floor(from / PAGESIZE);
			var toPage = Math.floor(to / PAGESIZE);

			while (data[fromPage * PAGESIZE] !== undefined && fromPage < toPage)
				fromPage++;

			while (data[toPage * PAGESIZE] !== undefined && fromPage < toPage)
				toPage--;

			if (fromPage > toPage || ((fromPage == toPage) && data[fromPage*PAGESIZE] !== undefined)) {
				// TODO:  look-ahead
				return;
			}
			if (urlBuilder == undefined || urlBuilder == null) {
				return;
			}
			var url = urlBuilder(fromPage, toPage, PAGESIZE, sortcol, sortdir);

			if (h_request != null)
				clearTimeout(h_request);

			h_request = setTimeout(function() {
				for (var i=fromPage; i<=toPage; i++)
					data[i*PAGESIZE] = null; // null indicates a 'requested but not available yet'

				onDataLoading.notify({from:from, to:to});

				req = $.jsonp({
					url: url,
					callbackParameter: "callback",
					cache: true,
					success: onSuccess,
					error: function(){
						onError(fromPage, toPage)
					}
					});
				req.fromPage = fromPage;
				req.toPage = toPage;
			}, 50);
		}


		function onError(fromPage,toPage) {
			alert("error loading pages " + fromPage + " to " + toPage);
		}

		function onSuccess(resp) {
			if (typeof resp.offset == "undefined" || resp.offset == null) {
				resp.offset = this.fromPage*PAGESIZE;
			}
			if (typeof resp.count == "undefined" || resp.count == null) {
				resp.count = resp.items.length;
			}
			var from = resp.offset, to = from + resp.count;
			data.length = parseInt(resp.total);

			for (var i = 0; i < resp[responseItemListName].length; i++) {
				data[from + i] = resp[responseItemListName][i];
				data[from + i].index = from + i;
			}

			req = null;

			onDataLoaded.notify({from:from, to:to});
		}


		function reloadData(from,to) {
			for (var i=from; i<=to; i++)
				delete data[i];

			ensureData(from,to);
		}


		function setSort(column,dir) {
			sortcol = column;
			sortdir = dir;
			clear();
		}
		
		function setUrlBuilder(fn) {
			urlBuilder = fn;
		}

		function setReponseItemListName(n) {
			responseItemListName = n;
		}


		init();

		return {
			// properties
			"data": data,

			// methods
			"clear": clear,
			"isDataLoaded": isDataLoaded,
			"ensureData": ensureData,
			"reloadData": reloadData,
			"setSort": setSort,
			"setUrlBuilder": setUrlBuilder,
			"setReponseItemListName": setReponseItemListName,

			// events
			"onDataLoading": onDataLoading,
			"onDataLoaded": onDataLoaded
		};
	}

	// Slick.Data.RemoteModel
	$.extend(true, window, { Slick: { Data: { RemoteModel: RemoteModel }}});
})(jQuery);
